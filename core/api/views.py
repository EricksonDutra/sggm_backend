from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.permissions import IsLiderOrReadOnly
from core.models import Escala, Evento, Instrumento, Musica, Musico
from core.services import NotificationService

from .serializers import (
    EscalaSerializer,
    EventoSerializer,
    InstrumentoSerializer,
    MusicaSerializer,
    MusicoSerializer,
)


class MusicoViewSet(viewsets.ModelViewSet):
    queryset = Musico.objects.all()
    serializer_class = MusicoSerializer

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def atualizar_fcm_token(self, request):
        """
        Atualizar token FCM do músico autenticado.
        POST /api/musicos/atualizar_fcm_token/
        Body: {"fcm_token": "token_aqui"}
        """
        token = request.data.get("fcm_token")

        if token is None:
            return Response(
                {"error": "fcm_token não fornecido"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 🔥 Tentar buscar por relacionamento User -> Musico
            if hasattr(request.user, "musico"):
                musico = request.user.musico
                print(f"✅ Músico encontrado via relacionamento: {musico.nome}")
            else:
                # Fallback: buscar por email
                musico = Musico.objects.get(email=request.user.email)
                print(f"✅ Músico encontrado via email: {musico.nome}")

            # Atualizar ou limpar token
            if token == "":
                musico.fcm_token = None
                musico.save()
                print(f"🗑️ Token FCM limpo para {musico.nome}")
                return Response(
                    {
                        "status": "Token limpo com sucesso",
                        "musico": musico.nome,
                        "musico_id": musico.id,
                    }
                )
            else:
                musico.fcm_token = token
                musico.save()
                print(f"✅ Token FCM atualizado para {musico.nome}")
                print(f"   Token (30 primeiros chars): {token[:30]}...")
                return Response(
                    {
                        "status": "Token atualizado com sucesso",
                        "musico": musico.nome,
                        "musico_id": musico.id,
                    }
                )

        except Musico.DoesNotExist:
            print(f"❌ Músico não encontrado para o usuário: {request.user.username}")
            print(f"   Email do usuário: {request.user.email}")
            return Response(
                {
                    "error": "Músico não encontrado para este usuário",
                    "details": "Certifique-se de que existe um músico com o mesmo email do usuário",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except AttributeError as e:
            print(f"❌ Erro de atributo: {e}")
            return Response(
                {"error": "Erro ao acessar dados do músico"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MusicaViewSet(viewsets.ModelViewSet):
    queryset = Musica.objects.all().order_by("titulo")
    serializer_class = MusicaSerializer


class EscalaViewSet(viewsets.ModelViewSet):
    queryset = Escala.objects.all()
    serializer_class = EscalaSerializer

    def create(self, request, *args, **kwargs):
        """Cria escala e envia notificação para o músico escalado"""
        try:
            # Criar escala
            response = super().create(request, *args, **kwargs)

            # Buscar escala criada
            escala = Escala.objects.get(id=response.data["id"])

            print("\n🎵 Nova escala criada:")
            print(f"   ID: {escala.id}")
            print(f"   Músico: {escala.musico.nome} (ID: {escala.musico.id})")
            print(f"   Evento: {escala.evento.nome}")
            print(
                f"   FCM Token do músico: {escala.musico.fcm_token[:30] if escala.musico.fcm_token else 'NULL'}..."
            )

            # 🔥 Verificar se músico tem token FCM
            if escala.musico.fcm_token:
                print(f"📤 Enviando notificação para {escala.musico.nome}...")

                # Enviar notificação
                sucesso = NotificationService.enviar_notificacao_escala(
                    musico=escala.musico, evento=escala.evento
                )

                if sucesso:
                    print("✅ Notificação enviada com sucesso!")
                else:
                    print("❌ Falha ao enviar notificação")
            else:
                print(f"⚠️ Músico {escala.musico.nome} não possui FCM token cadastrado")
                print(
                    "   O músico precisa fazer login no app para receber notificações"
                )

            return response

        except ValidationError as e:
            print(f"❌ Erro de validação: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return Response(
                {"detail": f"Erro ao criar escala: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all().order_by("-data_evento")
    serializer_class = EventoSerializer
    permission_classes = [IsLiderOrReadOnly]

    @action(detail=True, methods=["post"])
    def adicionar_repertorio(self, request, pk=None):
        """
        Adicionar músicas ao repertório do evento.
        POST /api/eventos/{id}/adicionar_repertorio/
        Body: {"musicas": [1, 2, 3]}
        """
        evento = self.get_object()
        musica_ids = request.data.get("musicas", [])

        if not musica_ids:
            return Response(
                {"error": "Nenhuma música fornecida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for mid in musica_ids:
            try:
                evento.repertorio.add(mid)
            except Exception as e:
                print(f"❌ Erro ao adicionar música {mid}: {e}")

        return Response(
            {
                "status": "Repertório atualizado",
                "total_musicas": evento.repertorio.count(),
            }
        )


class InstrumentoViewSet(viewsets.ModelViewSet):
    queryset = Instrumento.objects.all().order_by("nome")
    serializer_class = InstrumentoSerializer

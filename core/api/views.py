from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from core.api.permissions import IsLiderOrReadOnly, IsMusicoOwnerOrLider
from core.models import Escala, Evento, Instrumento, Musica, Musico
from core.services import NotificationService

from .serializers import (
    EscalaSerializer,
    EventoSerializer,
    InstrumentoSerializer,
    MusicaSerializer,
    MusicoCreateSerializer,
    MusicoSerializer,
)


# =====================================================
# JWT LOGIN CUSTOMIZADO
# =====================================================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para incluir dados do músico no token JWT.
    """

    def validate(self, attrs):
        # Obtém o token padrão
        data = super().validate(attrs)

        print(f"🔐 Login - User: {self.user.username}")

        # Adiciona informações extras do músico
        if hasattr(self.user, "musico"):
            musico = self.user.musico
            data["musico_id"] = musico.id
            data["nome"] = musico.nome
            data["username"] = self.user.username
            data["email"] = musico.email
            data["tipo_usuario"] = musico.tipo_usuario
            data["is_lider"] = musico.tipo_usuario in ["LIDER", "ADMIN"]
            data["is_admin"] = musico.tipo_usuario == "ADMIN"

            print(f"✅ Login bem-sucedido: {musico.nome} ({musico.tipo_usuario})")
        else:
            # Usuário sem perfil de músico
            data["musico_id"] = None
            data["nome"] = self.user.get_full_name() or self.user.username
            data["username"] = self.user.username
            data["email"] = self.user.email
            data["tipo_usuario"] = "USER"
            data["is_lider"] = False
            data["is_admin"] = self.user.is_superuser

            print(f"⚠️ Login de usuário sem perfil de músico: {self.user.username}")

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para login com JWT que retorna dados extras do músico.
    """

    serializer_class = MyTokenObtainPairSerializer


class MusicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar músicos.

    Endpoints:
    - GET /api/musicos/ - Lista músicos (apenas líderes/admins veem todos)
    - GET /api/musicos/{id}/ - Detalhes de um músico
    - POST /api/musicos/ - Criar novo músico
    - PUT/PATCH /api/musicos/{id}/ - Atualizar músico
    - DELETE /api/musicos/{id}/ - Remover músico (apenas admins)
    - GET /api/musicos/me/ - Perfil do músico autenticado
    - POST /api/musicos/atualizar_fcm_token/ - Atualizar token FCM
    - GET /api/musicos/{id}/escalas/ - Escalas de um músico
    """

    queryset = Musico.objects.select_related("user", "instrumento_principal").all()
    serializer_class = MusicoSerializer
    permission_classes = [IsAuthenticated, IsMusicoOwnerOrLider]

    def get_serializer_class(self):
        """Usa serializer específico para criação"""
        if self.action == "create":
            return MusicoCreateSerializer
        return MusicoSerializer

    def get_queryset(self):
        """
        Músicos comuns só veem seu próprio perfil.
        Líderes e admins veem todos.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Superuser vê todos
        if user.is_superuser:
            return queryset

        # Verificar se tem perfil de músico
        if hasattr(user, "musico"):
            musico = user.musico

            # Líder/Admin vê todos
            if musico.tipo_usuario in ["LIDER", "ADMIN"]:
                return queryset

            # Músico comum vê apenas seu perfil
            return queryset.filter(id=musico.id)

        # Usuário sem perfil de músico não vê nada
        return queryset.none()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retorna o perfil do músico autenticado.
        GET /api/musicos/me/

        Response: {
            "id": 1,
            "user": {...},
            "nome": "João Silva",
            "tipo_usuario": "MUSICO",
            ...
        }
        """
        if not hasattr(request.user, "musico"):
            return Response(
                {
                    "error": "Usuário não possui perfil de músico",
                    "details": "Este usuário não está vinculado a um perfil de músico",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(request.user.musico)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def atualizar_fcm_token(self, request):
        """
        Atualizar token FCM do músico autenticado.
        POST /api/musicos/atualizar_fcm_token/

        Body: {
            "fcm_token": "string" // ou "" para limpar
        }

        Response: {
            "status": "Token atualizado com sucesso",
            "musico": "João Silva",
            "musico_id": 1
        }
        """
        # Verificar se usuário tem perfil de músico
        if not hasattr(request.user, "musico"):
            return Response(
                {
                    "error": "Usuário não possui perfil de músico",
                    "details": "Este usuário não está vinculado a um perfil de músico",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        token = request.data.get("fcm_token")

        if token is None:
            return Response(
                {"error": "fcm_token não fornecido"}, status=status.HTTP_400_BAD_REQUEST
            )

        musico = request.user.musico

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

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def escalas(self, request, pk=None):
        """
        Retorna as escalas de um músico específico.
        GET /api/musicos/{id}/escalas/

        Query params:
        - futuras=true - Apenas escalas futuras
        - confirmadas=true - Apenas escalas confirmadas

        Response: [
            {
                "id": 1,
                "evento": {...},
                "instrumento_no_evento": "Violão",
                "confirmado": true,
                ...
            }
        ]
        """
        musico = self.get_object()
        escalas = musico.escalas.select_related(
            "evento", "instrumento_no_evento"
        ).order_by("-evento__data_evento")

        # Filtros opcionais
        if request.query_params.get("futuras") == "true":
            from django.utils.timezone import now

            escalas = escalas.filter(evento__data_evento__gte=now())

        if request.query_params.get("confirmadas") == "true":
            escalas = escalas.filter(confirmado=True)

        serializer = EscalaSerializer(escalas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def disponiveis(self, request):
        """
        Lista músicos disponíveis (status ATIVO e não afastados).
        GET /api/musicos/disponiveis/

        Response: [
            {
                "id": 1,
                "nome": "João Silva",
                "instrumento_principal": "Violão",
                ...
            }
        ]
        """
        # Apenas líderes e admins podem acessar
        if hasattr(request.user, "musico"):
            if request.user.musico.tipo_usuario not in ["LIDER", "ADMIN"]:
                return Response(
                    {"error": "Sem permissão para acessar esta lista"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        musicos_disponiveis = [
            musico for musico in self.get_queryset() if musico.esta_disponivel()
        ]

        serializer = self.get_serializer(musicos_disponiveis, many=True)
        return Response(serializer.data)


class MusicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar músicas do repertório.

    Endpoints:
    - GET /api/musicas/ - Lista todas as músicas
    - GET /api/musicas/{id}/ - Detalhes de uma música
    - POST /api/musicas/ - Criar nova música (apenas líderes/admins)
    - PUT/PATCH /api/musicas/{id}/ - Atualizar música (apenas líderes/admins)
    - DELETE /api/musicas/{id}/ - Remover música (apenas líderes/admins)
    """

    queryset = Musica.objects.all().order_by("titulo")
    serializer_class = MusicaSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]


class EscalaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar escalas de músicos em eventos.

    Endpoints:
    - GET /api/escalas/ - Lista escalas
    - GET /api/escalas/{id}/ - Detalhes de uma escala
    - POST /api/escalas/ - Criar nova escala (apenas líderes/admins)
    - PUT/PATCH /api/escalas/{id}/ - Atualizar escala
    - DELETE /api/escalas/{id}/ - Remover escala (apenas líderes/admins)
    - POST /api/escalas/{id}/confirmar/ - Confirmar presença
    """

    queryset = Escala.objects.select_related(
        "musico", "musico__user", "evento", "instrumento_no_evento"
    ).all()
    serializer_class = EscalaSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]

    def get_queryset(self):
        """
        Músicos comuns só veem suas próprias escalas.
        Líderes e admins veem todas.
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Superuser vê todas
        if user.is_superuser:
            return queryset

        # Verificar se tem perfil de músico
        if hasattr(user, "musico"):
            musico = user.musico

            # Líder/Admin vê todas
            if musico.tipo_usuario in ["LIDER", "ADMIN"]:
                return queryset

            # Músico comum vê apenas suas escalas
            return queryset.filter(musico=musico)

        return queryset.none()

    def create(self, request, *args, **kwargs):
        """
        Cria escala e envia notificação para o músico escalado.
        POST /api/escalas/

        Body: {
            "musico": 1,
            "evento": 1,
            "instrumento_no_evento": "Violão",
            "observacao": "..."
        }
        """
        try:
            # Criar escala
            response = super().create(request, *args, **kwargs)

            # Buscar escala criada com relacionamentos
            escala = Escala.objects.select_related(
                "musico", "musico__user", "evento"
            ).get(id=response.data["id"])

            print("\n🎵 Nova escala criada:")
            print(f"   ID: {escala.id}")
            print(f"   Músico: {escala.musico.nome} (ID: {escala.musico.id})")
            print(f"   Evento: {escala.evento.nome}")
            print(f"   Data: {escala.evento.data_evento}")
            print(
                f"   FCM Token: {escala.musico.fcm_token[:30] if escala.musico.fcm_token else 'NULL'}..."
            )

            # Verificar se músico tem token FCM
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
            print(f"❌ Erro inesperado: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return Response(
                {"detail": f"Erro ao criar escala: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def confirmar(self, request, pk=None):
        """
        Confirma presença do músico na escala.
        POST /api/escalas/{id}/confirmar/

        Body: {
            "confirmado": true
        }

        Response: {
            "status": "Presença confirmada",
            "escala_id": 1,
            "confirmado": true
        }
        """
        escala = self.get_object()

        # Verificar se o músico pode confirmar esta escala
        if hasattr(request.user, "musico"):
            musico = request.user.musico

            # Apenas o próprio músico, líderes ou admins podem confirmar
            if musico.id != escala.musico.id and musico.tipo_usuario not in [
                "LIDER",
                "ADMIN",
            ]:
                return Response(
                    {"error": "Você não pode confirmar a escala de outro músico"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"error": "Usuário não possui perfil de músico"},
                status=status.HTTP_403_FORBIDDEN,
            )

        confirmado = request.data.get("confirmado", True)
        escala.confirmado = confirmado
        escala.save()

        print(
            f"✅ Escala {escala.id} {'confirmada' if confirmado else 'desconfirmada'} por {musico.nome}"
        )

        return Response(
            {
                "status": f"Presença {'confirmada' if confirmado else 'desconfirmada'}",
                "escala_id": escala.id,
                "confirmado": escala.confirmado,
                "musico": escala.musico.nome,
                "evento": escala.evento.nome,
            }
        )


class EventoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar eventos.

    Endpoints:
    - GET /api/eventos/ - Lista eventos
    - GET /api/eventos/{id}/ - Detalhes de um evento
    - POST /api/eventos/ - Criar novo evento (apenas líderes/admins)
    - PUT/PATCH /api/eventos/{id}/ - Atualizar evento (apenas líderes/admins)
    - DELETE /api/eventos/{id}/ - Remover evento (apenas líderes/admins)
    - POST /api/eventos/{id}/adicionar_repertorio/ - Adicionar músicas
    - GET /api/eventos/proximos/ - Próximos eventos
    """

    queryset = (
        Evento.objects.select_related()
        .prefetch_related(
            "repertorio", "escalas", "escalas__musico", "escalas__instrumento_no_evento"
        )
        .all()
        .order_by("-data_evento")
    )
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsLiderOrReadOnly],
    )
    def adicionar_repertorio(self, request, pk=None):
        """
        Adicionar músicas ao repertório do evento.
        POST /api/eventos/{id}/adicionar_repertorio/

        Body: {
            "musicas": [1, 2, 3]
        }

        Response: {
            "status": "Repertório atualizado",
            "total_musicas": 3,
            "musicas_adicionadas": 3
        }
        """
        evento = self.get_object()
        musica_ids = request.data.get("musicas", [])

        if not musica_ids:
            return Response(
                {"error": "Nenhuma música fornecida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar se as músicas existem
        musicas_existentes = Musica.objects.filter(id__in=musica_ids)
        ids_encontrados = set(musicas_existentes.values_list("id", flat=True))
        ids_nao_encontrados = set(musica_ids) - ids_encontrados

        if ids_nao_encontrados:
            return Response(
                {
                    "error": "Algumas músicas não foram encontradas",
                    "musicas_nao_encontradas": list(ids_nao_encontrados),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Adicionar músicas ao repertório
        musicas_adicionadas = 0
        for musica in musicas_existentes:
            evento.repertorio.add(musica)
            musicas_adicionadas += 1
            print(f"✅ Música '{musica.titulo}' adicionada ao evento '{evento.nome}'")

        return Response(
            {
                "status": "Repertório atualizado",
                "total_musicas": evento.repertorio.count(),
                "musicas_adicionadas": musicas_adicionadas,
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def proximos(self, request):
        """
        Lista próximos eventos (futuros).
        GET /api/eventos/proximos/

        Query params:
        - limit=10 - Limitar quantidade de resultados

        Response: [
            {
                "id": 1,
                "nome": "Culto Domingo",
                "data_evento": "2026-02-16T19:00:00",
                ...
            }
        ]
        """
        from django.utils.timezone import now

        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10

        eventos = (
            self.get_queryset()
            .filter(data_evento__gte=now())
            .order_by("data_evento")[:limit]
        )

        serializer = self.get_serializer(eventos, many=True)
        return Response(serializer.data)


class InstrumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar instrumentos.

    Endpoints:
    - GET /api/instrumentos/ - Lista instrumentos
    - GET /api/instrumentos/{id}/ - Detalhes de um instrumento
    - POST /api/instrumentos/ - Criar novo instrumento (apenas líderes/admins)
    - PUT/PATCH /api/instrumentos/{id}/ - Atualizar instrumento (apenas líderes/admins)
    - DELETE /api/instrumentos/{id}/ - Remover instrumento (apenas líderes/admins)
    """

    queryset = Instrumento.objects.all().order_by("nome")
    serializer_class = InstrumentoSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]

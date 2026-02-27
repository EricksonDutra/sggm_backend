from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.utils.timezone import now
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from core.api.permissions import IsAutorOuLider, IsLiderOrReadOnly, IsMusicoOwnerOrLider
from core.models import (
    Artista,
    ComentarioPerformance,
    Escala,
    Evento,
    Instrumento,
    Musica,
    Musico,
    ReacaoComentario,
)
from core.services import NotificationService
from core.services.compartilhamento_service import CompartilhamentoService

from .serializers import (
    ArtistaSerializer,
    ComentarioPerformanceSerializer,
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

        # Log de login
        print(f"🔐 Login - User: {self.user.username}")

        # Adiciona informações extras do músico
        if hasattr(self.user, "musico"):
            musico = self.user.musico
            data.update(
                {
                    "musico_id": musico.id,
                    "nome": musico.nome,
                    "username": self.user.username,
                    "email": musico.email,
                    "tipo_usuario": musico.tipo_usuario,
                    "is_lider": musico.tipo_usuario in ["LIDER", "ADMIN"],
                    "is_admin": musico.tipo_usuario == "ADMIN",
                }
            )
            print(f"✅ Login bem-sucedido: {musico.nome} ({musico.tipo_usuario})")
        else:
            # Usuário sem perfil de músico
            data.update(
                {
                    "musico_id": None,
                    "nome": self.user.get_full_name() or self.user.username,
                    "username": self.user.username,
                    "email": self.user.email,
                    "tipo_usuario": "USER",
                    "is_lider": False,
                    "is_admin": self.user.is_superuser,
                }
            )
            print(f"⚠️ Login de usuário sem perfil de músico: {self.user.username}")

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para login com JWT que retorna dados extras do músico.
    """

    serializer_class = MyTokenObtainPairSerializer


# =====================================================
# MIXIN PARA LÓGICA COMUM DE PERMISSÕES
# =====================================================
class MusicoPermissionMixin:
    """
    Mixin para lógica comum de verificação de permissões de músicos.
    """

    def is_lider_or_admin(self, user):
        """Verifica se o usuário é líder ou admin."""
        if user.is_superuser:
            return True
        return hasattr(user, "musico") and user.musico.tipo_usuario in [
            "LIDER",
            "ADMIN",
        ]

    def get_musico_or_403(self, request):
        """Retorna o músico do request ou erro 403."""
        if not hasattr(request.user, "musico"):
            raise PermissionDenied("Usuário não possui perfil de músico")
        return request.user.musico


# =====================================================
# VIEWSETS
# =====================================================
class MusicoViewSet(MusicoPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar músicos com otimizações de query.
    """

    # ✅ Queryset como atributo de classe
    queryset = Musico.objects.select_related("user", "instrumento_principal").all()

    serializer_class = MusicoSerializer
    permission_classes = [IsAuthenticated, IsMusicoOwnerOrLider]

    # Filtros e ordenação
    filterset_fields = ["tipo_usuario", "status"]
    search_fields = ["nome", "email"]
    ordering_fields = ["nome", "created_at"]
    ordering = ["nome"]

    def get_queryset(self):
        """
        Filtra queryset por permissões do usuário.
        """
        # ✅ Usar super() para respeitar o queryset base
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

    def get_serializer_class(self):
        """✅ ATUALIZADO: Usa serializers específicos por ação e permissão"""

        # Criação: sempre usa MusicoCreateSerializer
        if self.action == "create":
            return MusicoCreateSerializer

        # Atualização: depende de quem está atualizando
        if self.action in ["update", "partial_update"]:
            # Importar aqui para evitar circular import
            from .serializers import (
                MusicoUpdateLiderSerializer,
                MusicoUpdateSelfSerializer,
            )

            user = self.request.user

            # Superuser sempre pode usar serializer completo
            if user.is_superuser:
                return MusicoUpdateLiderSerializer

            # Verificar se tem perfil de músico
            if hasattr(user, "musico"):
                musico = user.musico

                # Líder/Admin usa serializer completo
                if musico.tipo_usuario in ["LIDER", "ADMIN"]:
                    return MusicoUpdateLiderSerializer

                # Músico comum usa serializer limitado
                return MusicoUpdateSelfSerializer

            # Fallback
            return MusicoUpdateSelfSerializer

        # Leitura: usa serializer padrão
        return MusicoSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retorna o perfil do músico autenticado.
        GET /api/musicos/me/
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

        Body: {"fcm_token": "string"} ou "" para limpar
        """
        if not hasattr(request.user, "musico"):
            return Response(
                {"error": "Usuário não possui perfil de músico"},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = request.data.get("fcm_token")

        if token is None:
            return Response(
                {"error": "fcm_token não fornecido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        musico = request.user.musico

        # Atualizar ou limpar token
        if token == "":
            musico.fcm_token = None
            musico.save(update_fields=["fcm_token"])
            print(f"🗑️ Token FCM limpo para {musico.nome}")
            message = "Token limpo com sucesso"
        else:
            musico.fcm_token = token
            musico.save(update_fields=["fcm_token"])
            print(f"✅ Token FCM atualizado para {musico.nome}")
            print(f"   Token (30 primeiros chars): {token[:30]}...")
            message = "Token atualizado com sucesso"

        return Response(
            {
                "status": message,
                "musico": musico.nome,
                "musico_id": musico.id,
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def mudar_senha(self, request):
        """
        Mudar senha do usuário autenticado.
        POST /api/musicos/mudar_senha/

        Body: {
            "senha_atual": "string",
            "senha_nova": "string",
            "confirmar_senha": "string"
        }
        """
        if not hasattr(request.user, "musico"):
            return Response(
                {"error": "Usuário não possui perfil de músico"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        senha_atual = request.data.get("senha_atual")
        senha_nova = request.data.get("senha_nova")
        confirmar_senha = request.data.get("confirmar_senha")

        # Validações
        if not all([senha_atual, senha_nova, confirmar_senha]):
            return Response(
                {"error": "Todos os campos são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar se senha atual está correta
        if not user.check_password(senha_atual):
            return Response(
                {"error": "Senha atual incorreta"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar se senhas novas coincidem
        if senha_nova != confirmar_senha:
            return Response(
                {"error": "As senhas novas não coincidem"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar tamanho mínimo
        if len(senha_nova) < 8:
            return Response(
                {"error": "A senha deve ter no mínimo 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Atualizar senha
        user.set_password(senha_nova)
        user.save()

        print(f"🔐 Senha alterada para {user.musico.nome}")

        return Response(
            {
                "status": "Senha alterada com sucesso",
                "message": "Sua senha foi atualizada. Use a nova senha no próximo login.",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def escalas(self, request, pk=None):
        """
        Retorna as escalas de um músico específico com filtros opcionais.
        GET /api/musicos/{id}/escalas/?futuras=true&confirmadas=true
        """
        musico = self.get_object()

        # Otimização: select_related para evitar N+1 queries
        escalas = musico.escalas.select_related(
            "evento", "instrumento_no_evento"
        ).order_by("-evento__data_evento")

        # Filtros opcionais
        if request.query_params.get("futuras") == "true":
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

        Apenas líderes e admins podem acessar.
        """
        # Verificar permissão
        if not self.is_lider_or_admin(request.user):
            return Response(
                {"error": "Sem permissão para acessar esta lista"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Otimização: filtrar no banco de dados quando possível
        queryset = self.get_queryset().filter(status="ATIVO")

        # Para lógica complexa, filtrar em Python
        musicos_disponiveis = [
            musico for musico in queryset if musico.esta_disponivel()
        ]

        serializer = self.get_serializer(musicos_disponiveis, many=True)
        return Response(serializer.data)


class MusicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar músicas do repertório.
    """

    queryset = Musica.objects.all().order_by("titulo")

    serializer_class = MusicaSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]
    filterset_fields = ["compositor", "genero"]
    search_fields = ["titulo", "compositor"]
    ordering_fields = ["titulo", "compositor", "created_at"]
    ordering = ["titulo"]


class EscalaViewSet(MusicoPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar escalas de músicos em eventos.
    """

    # ✅ Queryset como atributo de classe
    queryset = Escala.objects.select_related(
        "musico",
        "musico__user",
        "musico__instrumento_principal",
        "evento",
        "instrumento_no_evento",
    ).all()

    serializer_class = EscalaSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]
    filterset_fields = ["confirmado", "evento", "musico"]
    ordering_fields = ["evento__data_evento", "created_at"]
    ordering = ["-evento__data_evento"]

    def get_queryset(self):
        """
        Filtra queries por permissões.
        """
        # ✅ Usar super() para respeitar o queryset base
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
        """
        try:
            # Criar escala
            response = super().create(request, *args, **kwargs)

            # Buscar escala criada com relacionamentos
            escala = self.get_queryset().get(id=response.data["id"])

            print("\n🎵 Nova escala criada:")
            print(f"   ID: {escala.id}")
            print(f"   Músico: {escala.musico.nome} (ID: {escala.musico.id})")
            print(f"   Evento: {escala.evento.nome}")
            print(f"   Data: {escala.evento.data_evento}")

            # Enviar notificação se músico tem token FCM
            if escala.musico.fcm_token:
                print(f"📤 Enviando notificação para {escala.musico.nome}...")

                sucesso = NotificationService.enviar_notificacao_escala(
                    musico=escala.musico, evento=escala.evento
                )

                if sucesso:
                    print("✅ Notificação enviada com sucesso!")
                else:
                    print("❌ Falha ao enviar notificação")
            else:
                print(f"⚠️ Músico {escala.musico.nome} não possui FCM token cadastrado")

            return response

        except DRFValidationError:
            raise

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

        Body: {"confirmado": true}
        """
        escala = self.get_object()

        # Verificar permissão
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

        # Atualizar confirmação
        confirmado = request.data.get("confirmado", True)
        escala.confirmado = confirmado
        escala.save(update_fields=["confirmado"])

        print(
            f"{'✅' if confirmado else '❌'} Escala {escala.id} "
            f"{'confirmada' if confirmado else 'desconfirmada'} por {musico.nome}"
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


class EventoViewSet(MusicoPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gerenciar eventos com otimizações agressivas.
    """

    queryset = Evento.objects.prefetch_related("repertorio").all()

    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]
    filterset_fields = ["tipo_evento", "local"]
    search_fields = ["nome", "descricao", "local"]
    ordering_fields = ["data_evento", "nome", "created_at"]
    ordering = ["-data_evento"]

    def get_queryset(self):
        """
        Otimização agressiva com prefetch customizado.
        """
        # ✅ Usar super() para respeitar o queryset base
        queryset = super().get_queryset()

        # Prefetch customizado para escalas
        escalas_prefetch = Prefetch(
            "escalas",
            queryset=Escala.objects.select_related(
                "musico",
                "musico__user",
                "musico__instrumento_principal",
                "instrumento_no_evento",
            ),
        )

        # Aplicar prefetch adicional
        return queryset.prefetch_related(escalas_prefetch)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsLiderOrReadOnly],
    )
    @action(detail=True, methods=["get"], url_path="compartilhar")
    def compartilhar(self, request, pk=None):
        """
        GET /api/eventos/{id}/compartilhar/
        Retorna o texto formatado da escala para compartilhamento (ex.: WhatsApp).
        """
        try:
            texto = CompartilhamentoService.gerar_texto_escala(int(pk))
            return Response({"texto": texto})
        except ValueError as e:
            return Response({"detail": str(e)}, status=404)

    def adicionar_repertorio(self, request, pk=None):
        """
        Adicionar músicas ao repertório do evento.
        POST /api/eventos/{id}/adicionar_repertorio/

        Body: {"musicas": [1, 2, 3]}
        """
        evento = self.get_object()
        musica_ids = request.data.get("musicas", [])

        # Validação: lista vazia
        if not musica_ids:
            return Response(
                {"error": "Nenhuma música fornecida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validação: tipo de dado
        if not isinstance(musica_ids, list):
            return Response(
                {"error": "O campo 'musicas' deve ser uma lista de IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar se as músicas existem
        musicas_existentes = Musica.objects.filter(id__in=musica_ids).values_list(
            "id", flat=True
        )

        ids_encontrados = set(musicas_existentes)
        ids_nao_encontrados = set(musica_ids) - ids_encontrados

        if ids_nao_encontrados:
            return Response(
                {
                    "error": "Algumas músicas não foram encontradas",
                    "musicas_nao_encontradas": sorted(list(ids_nao_encontrados)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Adicionar músicas ao repertório
        evento.repertorio.add(*ids_encontrados)

        print(
            f"✅ {len(ids_encontrados)} músicas adicionadas ao evento '{evento.nome}'"
        )

        return Response(
            {
                "status": "Repertório atualizado",
                "evento_id": evento.id,
                "evento_nome": evento.nome,
                "total_musicas": evento.repertorio.count(),
                "musicas_adicionadas": len(ids_encontrados),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["put"],
        permission_classes=[IsAuthenticated, IsLiderOrReadOnly],
    )
    def atualizar_repertorio(self, request, pk=None):
        """
        Substitui o repertório do evento pela lista enviada (replace completo).
        PUT /api/eventos/{id}/atualizar_repertorio/
        Body: { "musicas": [1, 2, 3] }
        """
        evento = self.get_object()
        musica_ids = request.data.get("musicas", [])

        if not isinstance(musica_ids, list):
            return Response(
                {"error": "O campo musicas deve ser uma lista de IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Valida se todas as músicas existem
        musicas_existentes = Musica.objects.filter(id__in=musica_ids).values_list(
            "id", flat=True
        )
        ids_nao_encontrados = set(musica_ids) - set(musicas_existentes)

        if ids_nao_encontrados:
            return Response(
                {
                    "error": "Algumas músicas não foram encontradas",
                    "musicas_nao_encontradas": sorted(list(ids_nao_encontrados)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # set() substitui toda a M2M — remove as antigas e adiciona as novas
        evento.repertorio.set(musica_ids)

        return Response(
            {
                "status": "Repertório atualizado",
                "evento_id": evento.id,
                "evento_nome": evento.nome,
                "total_musicas": evento.repertorio.count(),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def proximos(self, request):
        """
        Lista próximos eventos (futuros).
        GET /api/eventos/proximos/?limit=10
        """
        # Validar e limitar o parâmetro limit
        try:
            limit = int(request.query_params.get("limit", 10))
            limit = max(1, min(limit, 100))
        except (ValueError, TypeError):
            limit = 10

        # Usar get_queryset() para respeitar otimizações
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
    """

    # ✅ Queryset como atributo de classe
    queryset = Instrumento.objects.all().order_by("nome")

    serializer_class = InstrumentoSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]
    search_fields = ["nome", "categoria"]
    ordering_fields = ["nome", "categoria"]
    ordering = ["nome"]


class ArtistaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar artistas/bandas musicais.
    """

    queryset = Artista.objects.all().order_by("nome")
    serializer_class = ArtistaSerializer
    permission_classes = [IsAuthenticated, IsLiderOrReadOnly]
    search_fields = ["nome"]
    ordering_fields = ["nome", "criado_em"]
    ordering = ["nome"]

    def get_queryset(self):
        """Filtro opcional por nome para busca em tempo real"""
        queryset = super().get_queryset()
        nome = self.request.query_params.get("nome", None)

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        return queryset


# =====================================================
# COMENTARIOS DE PERFORMANCE
# =====================================================


class ComentarioPerformanceViewSet(MusicoPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet para comentários/feedbacks de performance por evento e música.
    """

    queryset = (
        ComentarioPerformance.objects.select_related("evento", "musica", "autor")
        .prefetch_related("reacoes")
        .all()
    )

    serializer_class = ComentarioPerformanceSerializer
    permission_classes = [IsAuthenticated, IsAutorOuLider]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros opcionais via query params
        evento_id = self.request.query_params.get("evento")
        musica_id = self.request.query_params.get("musica")

        if evento_id:
            queryset = queryset.filter(evento_id=evento_id)
        if musica_id:
            queryset = queryset.filter(musica_id=musica_id)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reagir(self, request, pk=None):
        """
        Toggle de curtida 👍 no comentário.
        POST /api/comentarios/{id}/reagir/
        """
        comentario = self.get_object()
        musico = self.get_musico_or_403(request)

        reacao, criada = ReacaoComentario.objects.get_or_create(
            comentario=comentario,
            musico=musico,
        )

        if not criada:
            reacao.delete()
            total = ReacaoComentario.objects.filter(comentario=comentario).count()

            return Response(
                {
                    "status": "removida",
                    "total_reacoes": total,
                },
                status=status.HTTP_200_OK,
            )

        total = ReacaoComentario.objects.filter(comentario=comentario).count()

        return Response(
            {
                "status": "adicionada",
                "total_reacoes": total,
            },
            status=status.HTTP_201_CREATED,
        )

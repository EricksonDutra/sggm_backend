from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.timezone import now

from .models import Escala, Evento, Instrumento, Musica, Musico


# =====================================================
# MUSICO
# =====================================================
class MusicoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "get_email",
        "tipo_usuario",
        "get_tipo_display",
        "status",
        "telefone",
    )
    list_filter = ("tipo_usuario", "status", "instrumento_principal")
    search_fields = ("nome", "user__email", "user__username", "telefone")
    ordering = ("nome",)
    readonly_fields = ("data_cadastro",)

    fieldsets = (
        ("Usuário", {"fields": ("user", "nome", "tipo_usuario")}),
        ("Contato", {"fields": ("telefone", "endereco")}),
        ("Informações Musicais", {"fields": ("instrumento_principal", "status")}),
        (
            "Inatividade",
            {
                "fields": (
                    "data_inicio_inatividade",
                    "data_fim_inatividade",
                    "motivo_inatividade",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Notificações", {"fields": ("fcm_token",), "classes": ("collapse",)}),
        ("Metadados", {"fields": ("data_cadastro",), "classes": ("collapse",)}),
    )

    def get_email(self, obj):
        return obj.email

    get_email.short_description = "Email"

    def get_tipo_display(self, obj):
        return obj.get_tipo_usuario_display()

    get_tipo_display.short_description = "Tipo"

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            return request.user.musico.tipo_usuario == "ADMIN"
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            musico_logado = request.user.musico
            if musico_logado.tipo_usuario in ["ADMIN", "LIDER"]:
                return True
            if obj and obj.id == musico_logado.id:
                return True
        return False

    def get_queryset(self, request):
        """Todos podem ver todos os músicos"""
        return super().get_queryset(request)


# =====================================================
# MUSICA
# =====================================================
class MusicaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "artista", "tom")
    search_fields = ("titulo", "artista")
    ordering = ("titulo",)
    fieldsets = (
        (
            "Informações da Música",
            {
                "fields": ("titulo", "artista", "tom", "link_cifra", "link_youtube"),
            },
        ),
    )


# =====================================================
# INLINE ESCALA (dentro do Evento)
# =====================================================
class EscalaInline(admin.TabularInline):
    model = Escala
    extra = 1
    autocomplete_fields = ("musico",)
    show_change_link = True
    fields = ("musico", "instrumento_no_evento", "confirmado", "observacao")


# =====================================================
# EVENTO
# =====================================================
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "data_evento", "local")
    search_fields = ("nome", "local")
    list_filter = ("tipo", "data_evento", "local")
    date_hierarchy = "data_evento"
    ordering = ("-data_evento",)

    autocomplete_fields = ("repertorio",)
    inlines = [EscalaInline]

    fieldsets = (
        (
            "Informações Principais",
            {
                "fields": ("nome", "tipo", "data_evento", "local"),
            },
        ),
        (
            "Detalhes",
            {
                "fields": ("descricao", "repertorio"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            return request.user.musico.tipo_usuario == "ADMIN"
        return request.user.groups.filter(name="Administradores").exists()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            return request.user.musico.tipo_usuario in ["LIDER", "ADMIN"]
        return request.user.groups.filter(
            name__in=["Lideres", "Administradores"]
        ).exists()

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            return request.user.musico.tipo_usuario in ["LIDER", "ADMIN"]
        return request.user.groups.filter(
            name__in=["Lideres", "Administradores"]
        ).exists()

    def get_queryset(self, request):
        """Todos podem ver todos os eventos"""
        return super().get_queryset(request)

    def get_fieldsets(self, request, obj=None):
        if hasattr(request.user, "musico"):
            if request.user.musico.tipo_usuario == "MUSICO":
                return (
                    (
                        "Informações do Evento",
                        {
                            "fields": (
                                "nome",
                                "tipo",
                                "data_evento",
                                "local",
                                "descricao",
                            ),
                        },
                    ),
                )
        return super().get_fieldsets(request, obj)


# =====================================================
# ESCALA
# =====================================================
class EscalaAdmin(admin.ModelAdmin):
    list_display = ("musico", "evento", "instrumento_no_evento", "confirmado")
    list_filter = ("confirmado", "evento__data_evento", "instrumento_no_evento")
    search_fields = ("musico__nome", "evento__nome")
    ordering = ("-evento__data_evento",)

    autocomplete_fields = ("musico", "evento")
    readonly_fields = ("criado_em",)

    fieldsets = (
        (
            "Relacionamentos",
            {
                "fields": ("musico", "evento"),
            },
        ),
        (
            "Detalhes da Escala",
            {
                "fields": ("instrumento_no_evento", "observacao", "confirmado"),
            },
        ),
        (
            "Metadados",
            {"fields": ("criado_em",), "classes": ("collapse",)},
        ),
    )

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            return request.user.musico.tipo_usuario in ["LIDER", "ADMIN"]
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if hasattr(request.user, "musico"):
            musico_logado = request.user.musico
            if musico_logado.tipo_usuario in ["LIDER", "ADMIN"]:
                return True
            if obj and obj.musico.id == musico_logado.id:
                return True
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and hasattr(request.user, "musico"):
            if request.user.musico.tipo_usuario == "MUSICO":
                readonly.extend(
                    ["musico", "evento", "instrumento_no_evento", "observacao"]
                )
        return readonly

    def get_queryset(self, request):
        """Todos podem ver todas as escalas"""
        return (
            super()
            .get_queryset(request)
            .select_related("musico", "evento", "instrumento_no_evento")
        )


# =====================================================
# INSTRUMENTO
# =====================================================
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)


# =====================================================
# CUSTOMIZAÇÃO GLOBAL DO ADMIN
# =====================================================
class CustomAdminSite(admin.AdminSite):
    site_header = "SGGM Administração"
    site_title = "SGGM"
    index_title = "Painel Administrativo"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        hoje = now()

        print("\n" + "=" * 50)
        print("🔍 [DASHBOARD] Iniciando dashboard_view")
        print(f"   User: {request.user.username}")

        # ✅ SEMPRE calcular estatísticas gerais PRIMEIRO (para todos)
        print("   📊 Calculando estatísticas gerais...")

        total_musicos = Musico.objects.all().count()
        total_musicas = Musica.objects.count()
        eventos_futuros = Evento.objects.filter(data_evento__gte=hoje).count()

        inicio_mes = hoje.replace(day=1)
        escalas_mes = Escala.objects.filter(
            evento__data_evento__month=hoje.month,
            evento__data_evento__year=hoje.year,
        ).count()

        print(f"   📊 Total Músicos: {total_musicos}")
        print(f"   📊 Total Músicas: {total_musicas}")
        print(f"   📊 Eventos futuros: {eventos_futuros}")
        print(f"   📊 Escalas no mês: {escalas_mes}")

        periodo_bloqueio = hoje - timedelta(days=15)

        musicas_recentes = Musica.objects.filter(
            eventos__data_evento__gte=periodo_bloqueio
        ).distinct()

        sugestao_repertorio = (
            Musica.objects.exclude(id__in=musicas_recentes)
            .annotate(total_eventos=Count("eventos"))
            .order_by("-total_eventos")[:5]
        )

        ranking_musicos = (
            Musico.objects.all()
            .annotate(total_escalas=Count("escalas"))
            .order_by("-total_escalas")[:5]
        )

        ranking_menos_escalados = (
            Musico.objects.all()
            .annotate(
                total_escalas=Count(
                    "escalas",
                    filter=Q(escalas__evento__data_evento__gte=inicio_mes),
                )
            )
            .order_by("total_escalas")[:5]
        )

        # Alerta de sobrecarga
        limite_consecutivo = 3
        sobrecarga = []

        for musico in Musico.objects.all():
            eventos_musico = (
                Escala.objects.filter(musico=musico)
                .select_related("evento")
                .order_by("evento__data_evento")
            )

            contador = 1
            maior_sequencia = 0
            ultima_data = None

            for escala in eventos_musico:
                data_atual = escala.evento.data_evento

                if ultima_data:
                    diferenca = (data_atual - ultima_data).days
                    if diferenca <= 7:
                        contador += 1
                    else:
                        contador = 1

                maior_sequencia = max(maior_sequencia, contador)
                ultima_data = data_atual

            if maior_sequencia >= limite_consecutivo:
                sobrecarga.append({"musico": musico, "sequencia": maior_sequencia})

        proximo_evento = (
            Evento.objects.filter(data_evento__gte=hoje).order_by("data_evento").first()
        )

        ranking_musicas = Musica.objects.annotate(
            total_eventos=Count("eventos")
        ).order_by("-total_eventos")[:5]

        print(f"   📊 Ranking músicas: {ranking_musicas.count()}")
        print(
            f"   📊 Próximo evento: {proximo_evento.nome if proximo_evento else 'Nenhum'}"
        )

        # ✅ Contexto base com todas as estatísticas (para todos)
        context = dict(
            self.each_context(request),
            is_musico_comum=False,  # Padrão
            total_musicos=total_musicos,
            total_musicas=total_musicas,
            eventos_futuros=eventos_futuros,
            escalas_mes=escalas_mes,
            proximo_evento=proximo_evento,
            ranking_musicas=ranking_musicas,
            sugestao_repertorio=sugestao_repertorio,
            ranking_musicos=ranking_musicos,
            ranking_menos_escalados=ranking_menos_escalados,
            sobrecarga=sobrecarga,
        )

        # ✅ DEPOIS adicionar dados pessoais se for músico comum
        if hasattr(request.user, "musico"):
            musico = request.user.musico
            is_musico_comum = musico.tipo_usuario == "MUSICO"
            print(f"   👤 Tipo usuário: {musico.tipo_usuario}")

            if is_musico_comum:
                minhas_escalas = Escala.objects.filter(musico=musico)

                # Adicionar dados pessoais ao contexto
                context.update(
                    {
                        "is_musico_comum": True,
                        "total_minhas_escalas": minhas_escalas.count(),
                        "escalas_mes_pessoal": minhas_escalas.filter(
                            evento__data_evento__month=hoje.month,
                            evento__data_evento__year=hoje.year,
                        ).count(),
                        "proxima_escala": minhas_escalas.filter(
                            evento__data_evento__gte=hoje
                        )
                        .select_related("evento", "instrumento_no_evento")
                        .order_by("evento__data_evento")
                        .first(),
                        "minhas_escalas_futuras": minhas_escalas.filter(
                            evento__data_evento__gte=hoje
                        )
                        .select_related("evento", "instrumento_no_evento")
                        .order_by("evento__data_evento")[:5],
                    }
                )

                print(f"   📊 Minhas escalas: {context['total_minhas_escalas']}")

        print("✅ [DASHBOARD] Contexto preparado")
        print(f"   Context keys: {list(context.keys())}")
        print("=" * 50 + "\n")

        return TemplateResponse(request, "admin/dashboard.html", context)

    def index(self, request, extra_context=None):
        return self.dashboard_view(request)


# =====================================================
# REGISTRO DOS MODELOS
# =====================================================
admin_site = CustomAdminSite(name="custom_admin")

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Musico, MusicoAdmin)
admin_site.register(Musica, MusicaAdmin)
admin_site.register(Evento, EventoAdmin)
admin_site.register(Escala, EscalaAdmin)
admin_site.register(Instrumento, InstrumentoAdmin)

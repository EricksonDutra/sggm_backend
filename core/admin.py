from django.contrib import admin
from django.utils.timezone import now

from .models import Escala, Evento, Instrumento, Musica, Musico

from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Q
from datetime import timedelta


# =====================================================
# MUSICO
# =====================================================


# @admin.register(Musico)
class MusicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone")
    search_fields = ("nome", "telefone")
    ordering = ("nome",)


# =====================================================
# MUSICA
# =====================================================
# @admin.register(Musica)
class MusicaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "artista")
    search_fields = ("titulo", "artista")
    ordering = ("titulo",)

    fieldsets = (
        ("Informações da Música", {
            "fields": ("titulo", "artista"),
        }),
    )


# =====================================================
# INLINE ESCALA (dentro do Evento)
# =====================================================
class EscalaInline(admin.TabularInline):
    model = Escala
    extra = 1
    autocomplete_fields = ("musico",)
    show_change_link = True


# =====================================================
# EVENTO
# =====================================================
# @admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_evento", "local")
    search_fields = ("nome", "local")
    list_filter = (
        "data_evento",
        "local",
    )
    date_hierarchy = "data_evento"
    ordering = ("-data_evento",)

    autocomplete_fields = ("repertorio",)
    inlines = [EscalaInline]

    fieldsets = (
        ("Informações Principais", {
            "fields": ("nome", "data_evento", "local"),
        }),
        ("Detalhes", {
            "fields": ("descricao", "repertorio"),
            "classes": ("collapse",),
        }),
    )

    # 🔐 Permissão: só Administradores podem excluir
    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name="Administradores").exists():
            return True
        return False

    # 👀 Músicos só veem eventos futuros
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.groups.filter(name="Músicos").exists():
            return qs.filter(data_evento__gte=now())

        return qs

    # 🎛 Admin adaptado por grupo
    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name="Músicos").exists():
            return (
                ("Informações do Evento", {
                    "fields": ("nome", "data_evento", "local"),
                }),
            )
        return super().get_fieldsets(request, obj)


# =====================================================
# ESCALA
# =====================================================
# @admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ("musico", "evento", "instrumento_no_evento")
    list_filter = ("evento", "instrumento_no_evento")
    search_fields = ("musico__nome", "evento__nome")
    ordering = ("evento",)

    autocomplete_fields = ("musico", "evento")
    raw_id_fields = ("musico",)

    fieldsets = (
        ("Relacionamentos", {
            "fields": ("musico", "evento"),
        }),
        ("Detalhes da Escala", {
            "fields": ("instrumento_no_evento",),
        }),
    )


# =====================================================
# INSTRUMENTO
# =====================================================
# @admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)


# =====================================================
# CUSTOMIZAÇÃO GLOBAL DO ADMIN
# =====================================================
# admin.site.site_header = "SGGM Administração"
# admin.site.site_title = "SGGM"
# admin.site.index_title = "Painel Administrativo"


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

        periodo_bloqueio = hoje - timedelta(days=15)

        # músicas usadas recentemente
        musicas_recentes = Musica.objects.filter(
            eventos__data_evento__gte=periodo_bloqueio
        ).distinct()

        # sugestão baseada no histórico mas evitando recentes
        sugestao_repertorio = (
            Musica.objects
            .exclude(id__in=musicas_recentes)
            .annotate(total_eventos=Count("eventos"))
            .order_by("-total_eventos")[:5]
        )

        ranking_musicos = (
            Musico.objects
            .annotate(total_escalas=Count("escalas"))
            .order_by("-total_escalas")[:5]
        )

        inicio_mes = now().replace(day=1)

        ranking_menos_escalados = (
            Musico.objects
            .annotate(
                total_escalas=Count(
                    "escalas",
                    filter=Q(escalas__evento__data_evento__gte=inicio_mes)
                )
            ) 
            .order_by("total_escalas")[:5]
        )

        # ==============================
        # 🚨 ALERTA DE SOBRECARGA
        # ==============================

        limite_consecutivo = 3

        eventos_ordenados = (
            Evento.objects
            .order_by("data_evento")
        )

        sobrecarga = []

        for musico in Musico.objects.all():
            eventos_musico = (
                Escala.objects
                .filter(musico=musico)
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
                    if diferenca <= 7:  # considera eventos próximos (ex: semana)
                        contador += 1
                    else:
                        contador = 1

                maior_sequencia = max(maior_sequencia, contador)
                ultima_data = data_atual

            if maior_sequencia >= limite_consecutivo:
                sobrecarga.append({
                    "musico": musico,
                    "sequencia": maior_sequencia
                })

        context = dict(
            self.each_context(request),
            total_musicos=Musico.objects.count(),
            total_musicas=Musica.objects.count(),
            eventos_futuros=Evento.objects.filter(
                data_evento__gte=hoje).count(),
            escalas_mes=Escala.objects.filter(
                evento__data_evento__month=hoje.month
            ).count(),
            proximo_evento=Evento.objects.filter(
                data_evento__gte=hoje
            ).order_by("data_evento").first(),
            ranking_musicas=(
                Musica.objects.annotate(total_eventos=Count(
                    "eventos")).order_by("-total_eventos")[:5]
            ),
            sugestao_repertorio=sugestao_repertorio,
            ranking_musicos=ranking_musicos,
            ranking_menos_escalados=ranking_menos_escalados,
            sobrecarga=sobrecarga,
        )

        return TemplateResponse(request, "admin/dashboard.html", context)

    def index(self, request, extra_content=None):
        return self.dashboard_view(request)


admin_site = CustomAdminSite(name="custom_admin")
admin_site.register(Musico, MusicoAdmin)
admin_site.register(Musica, MusicaAdmin)
admin_site.register(Evento, EventoAdmin)
admin_site.register(Escala, EscalaAdmin)
admin_site.register(Instrumento, InstrumentoAdmin)

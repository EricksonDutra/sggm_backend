from django.contrib import admin
from django.utils.timezone import now

from .models import Escala, Evento, Instrumento, Musica, Musico


# =====================================================
# MUSICO
# =====================================================
@admin.register(Musico)
class MusicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone")
    search_fields = ("nome", "telefone")
    ordering = ("nome",)


# =====================================================
# MUSICA
# =====================================================
@admin.register(Musica)
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
@admin.register(Evento)
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
@admin.register(Escala)
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
@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)


# =====================================================
# CUSTOMIZAÇÃO GLOBAL DO ADMIN
# =====================================================
admin.site.site_header = "SGGM Administração"
admin.site.site_title = "SGGM"
admin.site.index_title = "Painel Administrativo"

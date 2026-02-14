from rest_framework import permissions


class IsLiderOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Permitir leitura para qualquer usuário autenticado
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Para operações de escrita, verificar se é líder ou admin
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if hasattr(request.user, "musico"):
            return request.user.musico.is_lider()

        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permite acesso apenas para administradores.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if hasattr(request.user, "musico"):
            return request.user.musico.is_admin()

        return False


class IsMusicoOwnerOrLider(permissions.BasePermission):
    """
    Permite que músicos editem apenas seu próprio perfil.
    Líderes e admins podem editar qualquer perfil.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superuser tem acesso total
        if request.user.is_superuser:
            return True

        # Verificar se usuário tem perfil de músico
        if not hasattr(request.user, "musico"):
            return False

        musico_logado = request.user.musico

        # Líder/Admin pode editar qualquer perfil
        if musico_logado.is_lider():
            return True

        # Músico pode editar apenas seu próprio perfil
        return obj.id == musico_logado.id

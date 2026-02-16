from rest_framework import permissions


class IsLiderOrReadOnly(permissions.BasePermission):
    """
    Permite leitura para qualquer usuário autenticado.
    Escrita apenas para líderes ou superusuários.
    """

    def has_permission(self, request, view):
        # Usuário deve estar autenticado
        if not request.user.is_authenticated:
            return False

        # Permitir leitura para qualquer usuário autenticado
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusuários têm acesso total
        if request.user.is_superuser:
            return True

        # Para operações de escrita, verificar se é líder
        if hasattr(request.user, "musico"):
            return request.user.musico.is_lider()

        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permite acesso apenas para administradores ou superusuários.
    """

    def has_permission(self, request, view):
        # Usuário deve estar autenticado
        if not request.user.is_authenticated:
            return False

        # Superusuários têm acesso total
        if request.user.is_superuser:
            return True

        # Verificar se tem perfil de músico admin
        if hasattr(request.user, "musico"):
            return request.user.musico.is_admin()

        return False


class IsMusicoOwnerOrLider(permissions.BasePermission):
    """
    Permite que músicos editem apenas seu próprio perfil.
    Líderes e admins podem editar qualquer perfil.
    Todos podem ler (visualizar).
    """

    def has_permission(self, request, view):
        """
        Verificação no nível da view (antes de recuperar o objeto).
        """
        # Usuário deve estar autenticado
        if not request.user.is_authenticated:
            return False

        # Leitura permitida para todos os usuários autenticados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusuários têm acesso total
        if request.user.is_superuser:
            return True

        # Para escrita, verificar se usuário tem perfil de músico
        # (a verificação específica de propriedade será feita em has_object_permission)
        if hasattr(request.user, "musico"):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        """
        Verificação no nível do objeto (após recuperar o objeto específico).
        Este método só é chamado se has_permission retornar True.
        """
        # Leitura permitida para todos os usuários autenticados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusuários têm acesso total
        if request.user.is_superuser:
            return True

        # Verificar se usuário tem perfil de músico
        if not hasattr(request.user, "musico"):
            return False

        musico_logado = request.user.musico

        # Líder pode editar qualquer perfil
        if musico_logado.is_lider():
            return True

        # Músico comum pode editar apenas seu próprio perfil
        return obj.id == musico_logado.id


class IsMusicoOwner(permissions.BasePermission):
    """
    Permite que músicos editem apenas seus próprios dados.
    Útil para endpoints específicos onde apenas o próprio músico tem acesso.
    """

    def has_permission(self, request, view):
        """
        Verifica se o usuário está autenticado e tem perfil de músico.
        """
        if not request.user.is_authenticated:
            return False

        # Leitura permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # Para escrita, deve ter perfil de músico
        return hasattr(request.user, "musico")

    def has_object_permission(self, request, view, obj):
        """
        Verifica se o músico está acessando apenas seus próprios dados.
        """
        # Leitura permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # Verificar se é o próprio músico
        if hasattr(request.user, "musico"):
            return obj.id == request.user.musico.id

        return False


class CanEditOwnFields(permissions.BasePermission):
    """
    Permissão para permitir que músicos editem apenas campos específicos
    de seus próprios dados (disponibilidade, telefone, endereço, motivo).
    """

    # Campos que músicos comuns podem editar
    MUSICO_EDITABLE_FIELDS = {
        "disponivel",
        "telefone",
        "endereco",
        "motivo_indisponibilidade",
    }

    def has_permission(self, request, view):
        """
        Verificação no nível da view.
        """
        if not request.user.is_authenticated:
            return False

        # Leitura sempre permitida para autenticados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusuários e líderes podem editar tudo
        if request.user.is_superuser:
            return True

        if hasattr(request.user, "musico") and request.user.musico.is_lider():
            return True

        # Músicos comuns: verificar campos (será validado em has_object_permission)
        return hasattr(request.user, "musico")

    def has_object_permission(self, request, view, obj):
        """
        Verificação no nível do objeto com validação de campos.
        """
        # Leitura permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusuários têm acesso total
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, "musico"):
            return False

        musico_logado = request.user.musico

        # Líderes podem editar qualquer campo de qualquer músico
        if musico_logado.is_lider():
            return True

        # Músico comum: deve ser o próprio
        if obj.id != musico_logado.id:
            return False

        # Verificar se está tentando editar apenas campos permitidos
        if hasattr(request, "data"):
            submitted_fields = set(request.data.keys())
            if not submitted_fields.issubset(self.MUSICO_EDITABLE_FIELDS):
                return False

        return True

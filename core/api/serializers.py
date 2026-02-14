from django.contrib.auth.models import (
    User,  # ❌ CORRIGIDO: estava importando de gunicorn.config
)
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.models import Escala, Evento, Instrumento, Musica, Musico


# -------------------------
# USER
# -------------------------
class UserSerializer(serializers.ModelSerializer):
    """Serializer para dados básicos do usuário Django"""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id", "username"]


# -------------------------
# MUSICO
# -------------------------
class MusicoSerializer(serializers.ModelSerializer):
    """Serializer principal para leitura de músicos"""

    user = UserSerializer(read_only=True)
    instrumento_principal_nome = serializers.CharField(
        source="instrumento_principal.nome", read_only=True, allow_null=True
    )
    email = serializers.EmailField(source="user.email", read_only=True)
    tipo_usuario_display = serializers.CharField(
        source="get_tipo_usuario_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    esta_disponivel = serializers.BooleanField(read_only=True)
    esta_afastado = serializers.SerializerMethodField()

    class Meta:
        model = Musico
        fields = [
            "id",
            "user",
            "nome",
            "telefone",
            "email",
            "endereco",
            "instrumento_principal",
            "instrumento_principal_nome",
            "tipo_usuario",
            "tipo_usuario_display",
            "status",
            "status_display",
            "data_inicio_inatividade",
            "data_fim_inatividade",
            "motivo_inatividade",
            "data_cadastro",
            "esta_disponivel",
            "esta_afastado",
        ]
        read_only_fields = ["id", "data_cadastro", "user", "email"]

    def get_esta_afastado(self, obj):
        """Verifica se o músico está afastado no momento"""
        return obj.esta_afastado()


class MusicoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de músico com usuário"""

    username = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, min_length=8
    )
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Musico
        fields = [
            "username",
            "password",
            "email",
            "nome",
            "telefone",
            "endereco",
            "instrumento_principal",
            "tipo_usuario",
            "status",
        ]

    def validate_username(self, value):
        """Valida se username já existe"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate_email(self, value):
        """Valida se email já existe"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value

    def create(self, validated_data):
        # Extrair dados do usuário
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        email = validated_data.pop("email")

        # Dividir nome para first_name e last_name
        nome_completo = validated_data.get("nome", "")
        partes_nome = nome_completo.split()
        first_name = partes_nome[0] if partes_nome else ""
        last_name = " ".join(partes_nome[1:]) if len(partes_nome) > 1 else ""

        # Criar usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Criar músico vinculado
        musico = Musico.objects.create(user=user, **validated_data)

        print(f"✅ Novo músico criado: {musico.nome} (User: {user.username})")

        return musico


class MusicoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de músico (sem alterar usuário)"""

    class Meta:
        model = Musico
        fields = [
            "nome",
            "telefone",
            "endereco",
            "instrumento_principal",
            "tipo_usuario",
            "status",
            "data_inicio_inatividade",
            "data_fim_inatividade",
            "motivo_inatividade",
        ]

    def validate(self, data):
        """Validações customizadas"""
        # Se status for AFASTADO, validar datas
        if data.get("status") == "AFASTADO":
            if not data.get("data_inicio_inatividade") or not data.get(
                "data_fim_inatividade"
            ):
                raise serializers.ValidationError(
                    "Para status AFASTADO, é necessário informar data de início e fim."
                )

            if data["data_inicio_inatividade"] >= data["data_fim_inatividade"]:
                raise serializers.ValidationError(
                    "Data de início deve ser anterior à data de fim."
                )

        return data


# -------------------------
# MUSICA
# -------------------------
class MusicaSerializer(serializers.ModelSerializer):
    """Serializer para músicas do repertório"""

    total_eventos = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Musica
        fields = [
            "id",
            "titulo",
            "artista",
            "tom",
            "link_cifra",
            "link_youtube",
            "total_eventos",
        ]

    def validate_link_cifra(self, value):
        """Valida se o link da cifra é uma URL válida"""
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("Link da cifra deve ser uma URL válida.")
        return value

    def validate_link_youtube(self, value):
        """Valida se o link do YouTube é uma URL válida"""
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "Link do YouTube deve ser uma URL válida."
            )
        return value


# -------------------------
# INSTRUMENTO
# -------------------------
class InstrumentoSerializer(serializers.ModelSerializer):
    """Serializer para instrumentos musicais"""

    total_musicos = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Instrumento
        fields = ["id", "nome", "total_musicos"]


# -------------------------
# ESCALA
# -------------------------
class EscalaSerializer(serializers.ModelSerializer):
    """Serializer para escalas de músicos em eventos"""

    musico_nome = serializers.CharField(source="musico.nome", read_only=True)
    musico_telefone = serializers.CharField(source="musico.telefone", read_only=True)
    evento_nome = serializers.CharField(source="evento.nome", read_only=True)
    evento_data = serializers.DateTimeField(source="evento.data_evento", read_only=True)
    evento_local = serializers.CharField(source="evento.local", read_only=True)
    instrumento_nome = serializers.CharField(
        source="instrumento_no_evento.nome", read_only=True, allow_null=True
    )

    class Meta:
        model = Escala
        fields = [
            "id",
            "musico",
            "musico_nome",
            "musico_telefone",
            "evento",
            "evento_nome",
            "evento_data",
            "evento_local",
            "instrumento_no_evento",
            "instrumento_nome",
            "observacao",
            "confirmado",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]

    def validate(self, data):
        """Validações customizadas ao criar/atualizar escala"""
        musico = data.get("musico")
        evento = data.get("evento")

        # Verificar se músico está disponível
        if musico and not musico.esta_disponivel():
            raise serializers.ValidationError(
                f"O músico {musico.nome} não está disponível (status: {musico.get_status_display()})."
            )

        # Verificar duplicação (músico já escalado no mesmo evento)
        if musico and evento:
            instance_id = self.instance.id if self.instance else None
            if (
                Escala.objects.filter(musico=musico, evento=evento)
                .exclude(id=instance_id)
                .exists()
            ):
                raise serializers.ValidationError(
                    f"O músico {musico.nome} já está escalado para este evento."
                )

        return data


class EscalaCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para criar escalas (aceita nome do instrumento)"""

    instrumento_no_evento_nome = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Nome do instrumento (será criado se não existir)",
    )

    class Meta:
        model = Escala
        fields = [
            "musico",
            "evento",
            "instrumento_no_evento_nome",
            "observacao",
            "confirmado",
        ]

    def create(self, validated_data):
        # Extrair nome do instrumento
        nome_instr = validated_data.pop("instrumento_no_evento_nome", None)

        # Buscar ou criar instrumento
        instrumento = None
        if nome_instr and nome_instr.strip():
            instrumento, created = Instrumento.objects.get_or_create(
                nome__iexact=nome_instr.strip(),
                defaults={"nome": nome_instr.strip().title()},
            )
            if created:
                print(f"✅ Novo instrumento criado: {instrumento.nome}")

        return Escala.objects.create(
            instrumento_no_evento=instrumento, **validated_data
        )


# -------------------------
# EVENTO
# -------------------------
class EventoSerializer(serializers.ModelSerializer):
    """Serializer para eventos"""

    repertorio = MusicaSerializer(many=True, read_only=True)
    repertorio_ids = serializers.PrimaryKeyRelatedField(
        queryset=Musica.objects.all(),
        write_only=True,
        many=True,
        source="repertorio",
        required=False,
        help_text="IDs das músicas do repertório",
    )
    escalas = EscalaSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    total_escalas = serializers.IntegerField(
        source="escalas.count", read_only=True, required=False
    )
    total_musicas = serializers.IntegerField(
        source="repertorio.count", read_only=True, required=False
    )

    class Meta:
        model = Evento
        fields = [
            "id",
            "nome",
            "tipo",
            "tipo_display",
            "data_evento",
            "local",
            "descricao",
            "repertorio",
            "repertorio_ids",
            "escalas",
            "total_escalas",
            "total_musicas",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]

    def validate_data_evento(self, value):
        """Valida se a data do evento não é no passado"""
        from django.utils.timezone import now

        # Apenas validar para criação, não para atualização
        if not self.instance and value < now():
            raise serializers.ValidationError(
                "A data do evento não pode ser no passado."
            )

        return value


# -------------------------
# TOKEN JWT
# -------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado para JWT com informações do músico"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Adicionar informações básicas do usuário
        token["username"] = user.username
        token["email"] = user.email

        # Adicionar informações do músico ao token
        if hasattr(user, "musico"):
            musico = user.musico
            token["musico_id"] = musico.id
            token["nome"] = musico.nome
            token["tipo_usuario"] = musico.tipo_usuario
            token["is_lider"] = musico.is_lider()
            token["is_admin"] = musico.is_admin()
            token["status"] = musico.status
            token["instrumento_principal"] = (
                musico.instrumento_principal.nome
                if musico.instrumento_principal
                else None
            )
        else:
            token["is_lider"] = user.is_superuser
            token["is_admin"] = user.is_superuser

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Adicionar informações extras na resposta
        data["username"] = self.user.username
        data["email"] = self.user.email

        if hasattr(self.user, "musico"):
            musico = self.user.musico
            data["musico_id"] = musico.id
            data["nome"] = musico.nome
            data["tipo_usuario"] = musico.tipo_usuario
            data["tipo_usuario_display"] = musico.get_tipo_usuario_display()
            data["is_lider"] = musico.is_lider()
            data["is_admin"] = musico.is_admin()
            data["status"] = musico.status
            data["instrumento_principal"] = (
                {
                    "id": musico.instrumento_principal.id,
                    "nome": musico.instrumento_principal.nome,
                }
                if musico.instrumento_principal
                else None
            )
        else:
            data["is_lider"] = self.user.is_superuser
            data["is_admin"] = self.user.is_superuser
            data["message"] = "Usuário sem perfil de músico vinculado"

        return data

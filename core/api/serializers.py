from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.models import Escala, Evento, Instrumento, Musica, Musico


# -------------------------
# MUSICO
# -------------------------
class MusicoSerializer(serializers.ModelSerializer):
    instrumento_principal_nome = serializers.CharField(
        source="instrumento_principal.nome",
        read_only=True
    )

    class Meta:
        model = Musico
        fields = "__all__"


# -------------------------
# MUSICA
# -------------------------
class MusicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musica
        fields = ["id", "titulo", "artista", "tom", "link_cifra", "link_youtube"]


# -------------------------
# ESCALA
# -------------------------
class EscalaSerializer(serializers.ModelSerializer):
    musico_nome = serializers.CharField(source="musico.nome", read_only=True)
    evento_nome = serializers.CharField(source="evento.nome", read_only=True)

    instrumento_no_evento = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    instrumento_nome = serializers.CharField(
        source="instrumento_no_evento.nome",
        read_only=True
    )

    class Meta:
        model = Escala
        fields = [
            "id",
            "musico",
            "evento",
            "musico_nome",
            "evento_nome",
            "instrumento_no_evento",
            "instrumento_nome",
            "observacao",
        ]

    def create(self, validated_data):
        nome_instr = validated_data.pop("instrumento_no_evento", None)

        instrumento = None
        if nome_instr:
            instrumento, _ = Instrumento.objects.get_or_create(nome=nome_instr)

        return Escala.objects.create(
            instrumento_no_evento=instrumento,
            **validated_data
        )

# -------------------------
# EVENTO
# -------------------------
class EventoSerializer(serializers.ModelSerializer):
    repertorio = MusicaSerializer(many=True, read_only=True)

    repertorio_ids = serializers.PrimaryKeyRelatedField(
        queryset=Musica.objects.all(),
        write_only=True,
        many=True,
        source="repertorio",
        required=False
    )

    escalas = EscalaSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = [
            "id",
            "nome",
            "data_evento",
            "local",
            "descricao",
            "repertorio",
            "repertorio_ids",
            "escalas",
        ]

# -------------------------
# INSTRUMENTO
# -------------------------
class InstrumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrumento
        fields = ["id", "nome"]

# -------------------------
# TOKEN JWT
# -------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["is_lider"] = (
            user.groups.filter(name="Lideres").exists()
            or user.is_superuser
        )

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["username"] = self.user.username
        data["is_lider"] = (
            self.user.groups.filter(name="Lideres").exists()
            or self.user.is_superuser
        )

        return data

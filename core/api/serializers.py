from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import Escala, Evento, Instrumento, Musica, Musico


class MusicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musico
        fields = '__all__'


class MusicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musica
        fields = ['id', 'titulo', 'artista',
                  'tom', 'link_cifra', 'link_youtube']


class EscalaSerializer(serializers.ModelSerializer):
    # Campos de leitura para exibir o nome em vez do ID no JSON de resposta
    musico_nome = serializers.CharField(source='musico.nome', read_only=True)
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)

    class Meta:
        model = Escala
        fields = ['id', 'musico', 'evento', 'musico_nome',
                  'evento_nome', 'instrumento_no_evento', 'observacao']
        # Validadores extras se necessário
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Escala.objects.all(),
                fields=['musico', 'evento'],
                message="Este músico já está escalado para este evento."
            )
        ]


class EventoSerializer(serializers.ModelSerializer):
    repertorio = MusicaSerializer(many=True, read_only=True)
    repertorio_ids = serializers.PrimaryKeyRelatedField(
        queryset=Musica.objects.all(), write_only=True, many=True, source='repertorio'
    )

    escalas = EscalaSerializer(many=True, read_only=True)

    repertorio_ids = serializers.PrimaryKeyRelatedField(
        queryset=Musica.objects.all(),
        write_only=True,
        many=True,
        source='repertorio',
        required=False
    )

    class Meta:
        model = Evento
        fields = ['id', 'nome', 'data_evento', 'local',
                  'descricao', 'repertorio', 'repertorio_ids', 'escalas']


class InstrumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrumento
        fields = ['id', 'nome']


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['is_lider'] = user.groups.filter(
            name='Lideres').exists() or user.is_superuser

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['username'] = self.user.username
        data['is_lider'] = self.user.groups.filter(
            name='Lideres').exists() or self.user.is_superuser

        return data

from rest_framework import serializers
from .models import Musicos, Eventos, Escalas, Musicas, EscalaRepertorio

class MusicosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musicos
        fields = '__all__'  # Você pode especificar os campos que deseja incluir, se preferir

class EventosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eventos
        fields = '__all__'

class EscalasSerializer(serializers.ModelSerializer):
    nome_musico = serializers.SerializerMethodField()
    nome_evento = serializers.SerializerMethodField()

    class Meta:
        model = Escalas
        fields = ['escalaId', 'dataEscala', 'musico', 'evento', 'nome_musico', 'nome_evento']
    
    def get_nome_musico(self, obj):
        return obj.musico.nome if obj.musico else None
    
    def get_nome_evento(self, obj):
        return obj.evento.nome if obj.evento else None

class MusicasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musicas
        fields = '__all__'

class EscalaRepertorioSerializer(serializers.ModelSerializer):
    nome_escala = serializers.SerializerMethodField()
    nome_musica = serializers.SerializerMethodField()
    nome_musico = serializers.SerializerMethodField()
    nome_evento = serializers.SerializerMethodField()

    class Meta:
        model = EscalaRepertorio
        fields = ['escala_repertorioId', 'escalaId', 'musicaId', 'nome_escala', 'nome_musica', 'nome_musico', 'nome_evento']

    def get_nome_escala(self, obj):
        return obj.escalaId.evento.nome if obj.escalaId and obj.escalaId.evento else None
    
    def get_nome_musica(self, obj):
        return obj.musicaId.nome if obj.musicaId else None
    
class EscalaSerializer(serializers.ModelSerializer):
    nome_escala = serializers.SerializerMethodField()
    nome_musica = serializers.SerializerMethodField()
    nome_musico = serializers.SerializerMethodField()
    nome_evento = serializers.SerializerMethodField()

    class Meta:
        model = Escalas
        fields = ['escalaId', 'escalaId', 'musicaId', 'nome_escala', 'nome_musica', 'nome_musico', 'nome_evento']

    def get_nome_escala(self, obj):
        return obj.escalaId.evento.nome if obj.escalaId and obj.escalaId.evento else None
    
    def get_nome_musica(self, obj):
        return obj.musicaId.nome if obj.musicaId else None
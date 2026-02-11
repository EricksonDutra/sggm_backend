from core.api.permissions import IsLiderOrReadOnly
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Escala, Evento, Instrumento, Musica, Musico

from .serializers import (
    EscalaSerializer,
    EventoSerializer,
    InstrumentoSerializer,
    MusicaSerializer,
    MusicoSerializer,
)


class MusicoViewSet(viewsets.ModelViewSet):
    queryset = Musico.objects.all()
    serializer_class = MusicoSerializer


class MusicaViewSet(viewsets.ModelViewSet):
    queryset = Musica.objects.all().order_by('titulo')
    serializer_class = MusicaSerializer


class EscalaViewSet(viewsets.ModelViewSet):
    queryset = Escala.objects.all()
    serializer_class = EscalaSerializer

    # Sobrescrevemos o create para usar nosso Service (opcional, mas recomendado para Clean Arch)
    def create(self, request, *args, **kwargs):
        try:
            # Aqui poderíamos chamar GerenciadorEscala.adicionar_musico...
            # Mas como o Serializer já valida uniqueness, podemos manter o padrão do DRF
            # ou forçar o uso do service se houver lógica complexa extra.
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all().order_by('-data_evento')
    serializer_class = EventoSerializer

    @action(detail=True, methods=['post'])
    def adicionar_repertorio(self, request, pk=None):
        """Endpoint extra: /api/eventos/{id}/adicionar_repertorio/"""
        evento = self.get_object()
        musica_ids = request.data.get('musicas', [])
        for mid in musica_ids:
            evento.repertorio.add(mid)
        return Response({'status': 'Repertório atualizado'})


class InstrumentoViewSet(viewsets.ModelViewSet):
    queryset = Instrumento.objects.all().order_by('nome')
    serializer_class = InstrumentoSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all().order_by('-data_evento')
    serializer_class = EventoSerializer
    permission_classes = [IsLiderOrReadOnly]

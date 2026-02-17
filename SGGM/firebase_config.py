import os

import firebase_admin
from django.conf import settings
from firebase_admin import credentials


def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK.
    Deve ser chamado apenas uma vez ao iniciar o Django.
    """
    if not firebase_admin._apps:
        try:
            # Caminho para o arquivo de credenciais
            cred_path = os.path.join(
                settings.BASE_DIR, "SGGM", "serviceAccountKey.json"
            )

            if not os.path.exists(cred_path):
                print(
                    f"❌ ERRO: Arquivo serviceAccountKey.json não encontrado em: {cred_path}"
                )
                print("   Baixe o arquivo do Firebase Console e coloque neste caminho.")
                return False

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

            print("✅ Firebase Admin SDK inicializado com sucesso!")
            print(f"   Credenciais: {cred_path}")
            return True

        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")
            import traceback

            traceback.print_exc()
            return False
    else:
        print("ℹ️ Firebase Admin SDK já está inicializado")
        return True

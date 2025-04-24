```ascii
  ________ ____ ___._______   _______________.____     
 /  _____/|    |   \   \   \ /   /\__    ___/|    |    
/   \  ___|    |   /   |\   Y   /   |    |   |    |    
\    \_\  \    |  /|   | \     /    |    |   |    |___ 
 \______  /______/ |___|  \___/     |____|   |_______ \
        \/                                           \/

         🖕   M U L T I V E R S A   B Y P A S S   🖕
```

# Multiversa Bypass

Para os amigos do peito!

## Configuração

1.  **Instalar Dependências:**
    Abra o terminal na pasta do projeto e execute:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Obter Chave da API Google Gemini:**
    *   Acesse o [Google AI Studio](https://aistudio.google.com/).
    *   Faça login com sua conta Google.
    *   Clique em "Get API key" -> "Create API key in new project".
    *   Copie a chave gerada.

3.  **Configurar Variáveis de Ambiente:**
    *   Renomeie o arquivo `.env.example` (se existir) para `.env`.
    *   Abra o arquivo `.env` e preencha os seguintes valores:
        ```dotenv
        MOODLE_USERNAME="seu_usuario_moodle"
        MOODLE_PASSWORD="sua_senha_moodle"
        GEMINI_API_KEY="sua_chave_api_gemini_aqui"
        ```
    *   Substitua pelos seus dados reais.

## Execução

1.  Abra o terminal na pasta do projeto.
2.  Execute o script principal:
    ```bash
    python main.py
    ```



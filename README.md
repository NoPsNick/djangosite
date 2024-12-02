---

# Django Site

> Um site feito em Django para marketing digital.

---

## 🚧 **Ajustes e Melhorias**

O projeto foi finalizado, mas as próximas atualizações poderão incluir:

- [x] Otimização de consultas no banco de dados.  
- [x] Documentação e refatoração dos códigos.  
- [ ] Otimizar o Django Admin *(pendente, sujeito a avaliação).*  

---

## 💻 **Pré-requisitos**

Antes de começar, verifique se você atende aos seguintes requisitos:

- Um sistema operacional **Windows**, **Linux** ou **macOS**.
- **Python** na versão mais recente instalado. [Baixar Python](https://www.python.org/downloads/)  
- Um sistema gerenciador de banco de dados (SGDB), preferencialmente **PostgreSQL**. [Baixar PostgreSQL](https://www.postgresql.org/download/)  

---

## 🚀 **Instalando o Django Site**

### **Passo 1: Clonar o repositório**

Execute no terminal:  

```bash
git clone https://github.com/NoPsNick/djangosite.git
cd djangosite
```

---

### **Passo 2: Configurar o ambiente virtual**

#### **Linux e macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

#### **Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

---

### **Passo 3: Instalar as dependências**

Com o ambiente virtual ativado, instale os pacotes necessários:  

```bash
pip install -r requirements.txt
```

---

## 🔐 **Configuração do Arquivo `.env`**

Para que o projeto funcione corretamente, configure um arquivo `.env` no diretório raiz do projeto.

### **Passo 1: Criar o arquivo**

#### **Windows**

```bash
type nul > .env
```

#### **Linux e macOS**

```bash
touch .env
```

---

### **Passo 2: Configurar variáveis de ambiente**

Adicione o seguinte conteúdo ao arquivo `.env`:

```env
USERNAME=O usuário do banco de dados, normalmente postgres
PASSWORD=A senha do banco de dados
DATABASE=Nome do banco de dados
HOST=localhost
PORT=5432
ENGINE=django.db.backends.postgresql
SECRET_KEY=Chave secreta do Django
```

Preencha os valores de acordo com o seu ambiente.

- **`USERNAME`**: Nome de usuário do banco (ex.: `postgres`).  
- **`PASSWORD`**: Senha do banco de dados.  
- **`DATABASE`**: Nome do banco usado pelo projeto.  
- **`HOST`**: Geralmente `localhost`.  
- **`PORT`**: Normalmente `5432` para PostgreSQL.  
- **`ENGINE`**: Não altere, deve ser `django.db.backends.postgresql`.  
- **`SECRET_KEY`**: Uma chave secreta única para o Django (gere uma com [Djecrety](https://djecrety.ir)).  

⚠️ **Certifique-se de adicionar o `.env` ao `.gitignore` para proteger informações sensíveis.**

---

## ☕ **Usando o Django Site**
⚠️ CERTIFIQUE-SE DE TER FEITO OS PASSOS ACIMA.
Para iniciar o servidor de desenvolvimento, use o comando:  

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Acesse o site no navegador em **[http://localhost:8000](http://localhost:8000)**.

---

## 📝 **Licença**

Este projeto está sob licença. Consulte o arquivo [LICENSE.md](LICENSE.md) para mais detalhes.

---

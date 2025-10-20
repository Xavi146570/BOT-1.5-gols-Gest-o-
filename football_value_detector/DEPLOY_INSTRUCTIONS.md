# 🚀 Guia Completo de Deploy no Render

Este guia detalha **passo a passo** como fazer deploy do Football Value Detector no Render (plataforma gratuita).

---

## 📋 **ÍNDICE**

1. [Pré-requisitos](#pré-requisitos)
2. [Obter API Key da API-Football](#obter-api-key)
3. [Preparar Repositório GitHub](#preparar-repositório)
4. [Criar Conta no Render](#criar-conta-no-render)
5. [Deploy do Web Service](#deploy-do-web-service)
6. [Configurar Variáveis de Ambiente](#configurar-variáveis)
7. [Verificar Deploy](#verificar-deploy)
8. [Manter App Ativo 24/7](#manter-ativo)
9. [Logs e Monitoramento](#logs-e-monitoramento)
10. [Troubleshooting](#troubleshooting)

---

## 1️⃣ **PRÉ-REQUISITOS**

Antes de começar, você precisa:

✅ **Conta GitHub** (gratuita)  
✅ **Repositório com os 20 arquivos** do projeto  
✅ **Conta na API-Football** (plano gratuito)  
✅ **Conta no Render** (gratuita)  

---

## 2️⃣ **OBTER API KEY DA API-FOOTBALL**

### **Passo 1: Criar Conta**

1. Acesse: https://www.api-football.com/
2. Clique em **"Get Your Free API Key"**
3. Preencha o formulário:
   - Nome
   - Email
   - Senha
4. Confirme email

### **Passo 2: Obter API Key**

1. Faça login em: https://dashboard.api-football.com/
2. No dashboard, copie sua **API Key**
3. Formato: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (32 caracteres)

### **Passo 3: Verificar Plano Gratuito**

✅ **Plano Free inclui:**
- 100 requisições/dia
- Acesso a todas ligas
- Odds em tempo real
- Estatísticas completas

⚠️ **Importante:** 100 req/dia é suficiente para analisar 5-10 ligas principais diariamente

---

## 3️⃣ **PREPARAR REPOSITÓRIO GITHUB**

### **Verificar Arquivos Necessários**

Certifique-se que seu repositório tem **todos os 20 arquivos**:

### **NÃO Commitar o Arquivo .env**

⚠️ **NUNCA faça commit do arquivo `.env` com sua API Key!**

O `.gitignore` já está configurado para ignorá-lo:
---

## 4️⃣ **CRIAR CONTA NO RENDER**

### **Passo 1: Acessar Render**

1. Acesse: https://render.com
2. Clique em **"Get Started"**

### **Passo 2: Conectar GitHub**

1. Clique em **"Sign up with GitHub"**
2. Autorize Render a acessar seu GitHub
3. Selecione:
   - ✅ **All repositories** (recomendado)
   - OU específico: `football_value_detector`

### **Passo 3: Confirmar Email**

1. Verifique seu email
2. Clique no link de confirmação
3. Complete seu perfil (opcional)

---

## 5️⃣ **DEPLOY DO WEB SERVICE**

### **Passo 1: Novo Web Service**

1. No dashboard do Render, clique em **"New +"**
2. Selecione **"Web Service"**

### **Passo 2: Conectar Repositório**

1. Procure por: `football_value_detector`
2. Clique em **"Connect"**

### **Passo 3: Configurar Service**

Preencha os campos:

**Name:**
(Ou `master`, dependendo do seu repo)

**Runtime:**
✅ **IMPORTANTE:** Selecione **Docker**, NÃO Python!

**Instance Type:**
### **Passo 4: Deixar Campos Padrão**

❌ **NÃO preencha:**
- Build Command (Docker usa Dockerfile)
- Start Command (Docker usa CMD do Dockerfile)

---

## 6️⃣ **CONFIGURAR VARIÁVEIS DE AMBIENTE**

### **Antes de Criar o Service**

Na seção **"Environment Variables"**:

1. Clique em **"Add Environment Variable"**

2. **Variável 1:**
   - Key: `API_FOOTBALL_KEY`
   - Value: `sua_api_key_aqui` (cole sua API Key)

3. **Variável 2 (Opcional):**
   - Key: `PORT`
   - Value: `10000`
   (Render define automaticamente, mas pode especificar)

**Exemplo:**
API_FOOTBALL_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6 PORT=1000

## 7️⃣ **CRIAR E VERIFICAR DEPLOY**

### **Passo 1: Iniciar Deploy**

1. Revise todas configurações
2. Clique em **"Create Web Service"**
3. Render iniciará o build automaticamente

### **Passo 2: Acompanhar Build**

O processo leva **3-7 minutos**:



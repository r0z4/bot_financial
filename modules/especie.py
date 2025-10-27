from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from database import get_db
from datetime import datetime
import re

VALOR_ESPECIE = range(1)
EDITA_ID, EDITA_NOVO_VALOR = range(2)
EXCLUIR_ID = range(1)

# Adicionar espécie
async def pedir_valor_especie(update, context):
    await update.message.reply_text("Informe o valor em espécie recebido ou depositado (ex: 100):")
    return VALOR_ESPECIE

async def salvar_valor_especie(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    try:
        valor = float(update.message.text.replace(",", "."))
        data_hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res = db.especie.insert_one({
            "user_id": user_id,
            "valor": valor,
            "data": data_hoje        # <-- agora com hora:minuto:segundo
        })
        await update.message.reply_text(
            f"Dinheiro em espécie somado: R$ {valor:.2f}\nData: {data_hoje}\nID: {res.inserted_id}"
        )
    except Exception:
        await update.message.reply_text("Valor inválido! Apenas números.")
        return VALOR_ESPECIE
    return ConversationHandler.END


especie_handler = ConversationHandler(
    entry_points=[CommandHandler('especie', pedir_valor_especie)],
    states={VALOR_ESPECIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_valor_especie)]},
    fallbacks=[]
)

# Consulta saldo espécie
async def saldo_especie(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    total = sum(e['valor'] for e in db.especie.find({"user_id": user_id}))
    await update.message.reply_text(f"Total em espécie: R$ {total:.2f}")

saldo_especie_handler = CommandHandler('saldo_especie', saldo_especie)

# Editar espécie
async def pedir_id_editar(update, context):
    await update.message.reply_text("Informe o ID do lançamento de espécie que deseja editar (/listar_especie mostra todos):")
    return EDITA_ID

async def pedir_novo_valor(update, context):
    id_raw = update.message.text.strip()
    match = re.search(r'([0-9a-fA-F]{24})', id_raw)
    if match:
        context.user_data['editar_id'] = match.group(1)
        await update.message.reply_text("Qual o novo valor?")
        return EDITA_NOVO_VALOR
    else:
        await update.message.reply_text("ID inválido! Copie o ID corretamente ou use apenas o código.")
        return EDITA_ID

async def salvar_edicao_especie(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    eid = context.user_data['editar_id']
    try:
        novo_valor = float(update.message.text.replace(",", "."))
        result = db.especie.update_one(
            {"_id": __import__("bson").ObjectId(eid), "user_id": user_id},
            {"$set": {"valor": novo_valor}}
        )
        if result.modified_count:
            await update.message.reply_text("Valor em espécie atualizado com sucesso!")
        else:
            await update.message.reply_text("ID não encontrado ou sem permissão.")
    except Exception:
        await update.message.reply_text("ID ou valor inválido.")
        return EDITA_NOVO_VALOR
    return ConversationHandler.END

editar_especie_handler = ConversationHandler(
    entry_points=[CommandHandler('editar_especie', pedir_id_editar)],
    states={
        EDITA_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_novo_valor)],
        EDITA_NOVO_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_edicao_especie)],
    },
    fallbacks=[]
)

# Excluir espécie
async def pedir_id_excluir(update, context):
    await update.message.reply_text("Informe o ID do lançamento de espécie que deseja excluir (/listar_especie mostra todos):")
    return EXCLUIR_ID

async def excluir_especie(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    id_raw = update.message.text.strip()
    match = re.search(r'([0-9a-fA-F]{24})', id_raw)
    if not match:
        await update.message.reply_text("ID inválido! Copie o ID corretamente, pode colar como está.")
        return EXCLUIR_ID
    eid = match.group(1)
    try:
        result = db.especie.delete_one(
            {"_id": __import__("bson").ObjectId(eid), "user_id": user_id}
        )
        if result.deleted_count:
            await update.message.reply_text("Valor em espécie excluído com sucesso!")
        else:
            await update.message.reply_text("ID não encontrado ou sem permissão.")
    except Exception:
        await update.message.reply_text("ID inválido!")
        return EXCLUIR_ID
    return ConversationHandler.END

excluir_especie_handler = ConversationHandler(
    entry_points=[CommandHandler('excluir_especie', pedir_id_excluir)],
    states={EXCLUIR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, excluir_especie)]},
    fallbacks=[]
)

# Listar todos os lançamentos espécie COM DATA + HORA
async def listar_especie(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    lista = list(db.especie.find({"user_id": user_id}))
    if not lista:
        await update.message.reply_text("Nenhum lançamento em espécie.")
        return
    msg = "💵 Lançamentos em espécie:\n\n"
    for e in lista:
        msg += f"• Valor: R$ {e['valor']:.2f} | Data: {e.get('data','-')} | ID: {str(e['_id'])}\n"
    await update.message.reply_text(msg)

listar_especie_handler = CommandHandler('listar_especie', listar_especie)

from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from database import get_db

NOME_META, VALOR_META = range(2)

# Adicionar meta
async def pedir_nome_meta(update, context):
    await update.message.reply_text("Qual o nome da meta? (ex: Viagem, Notebook, Investimento)")
    return NOME_META

async def pedir_valor_meta(update, context):
    context.user_data['nome_meta'] = update.message.text
    await update.message.reply_text("Qual o valor da meta?")
    return VALOR_META

async def salvar_meta(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    nome = context.user_data['nome_meta']
    try:
        valor = float(update.message.text.replace(",", "."))
        db.metas.insert_one({
            "user_id": user_id,
            "nome": nome,
            "valor": valor
        })
        await update.message.reply_text(f"Meta '{nome}' cadastrada com valor R$ {valor:.2f}")
    except:
        await update.message.reply_text("Valor inválido. Só números.")
        return VALOR_META
    return ConversationHandler.END

metas_handler = ConversationHandler(
    entry_points=[CommandHandler('meta', pedir_nome_meta)],
    states={
        NOME_META: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_valor_meta)],
        VALOR_META: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_meta)]
    },
    fallbacks=[]
)


# Listar metas
async def listar_metas(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    metas = list(db.metas.find({"user_id": user_id}))
    if not metas:
        await update.message.reply_text("Nenhuma meta cadastrada ainda.")
        return
    msg = "🎯 *Suas Metas:*\n\n"
    for meta in metas:
        msg += f"- {meta['nome']}: R$ {meta['valor']:.2f}\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

listar_metas_handler = CommandHandler('listar_metas', listar_metas)

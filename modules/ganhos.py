from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from database import get_db
from bson import ObjectId

VALOR_GANHO, CATEGORIA_GANHO, CONTA_GANHO, DATA_GANHO = range(4)
VALOR_NOVO_G, CATEGORIA_NOVA_G, CONTA_NOVA_G, DATA_NOVA_G = range(4,8)

async def iniciar_ganho(update, context):
    await update.message.reply_text("💵 Qual o valor do ganho?")
    return VALOR_GANHO

async def salvar_valor_ganho(update, context):
    valor = update.message.text.replace(",", ".")
    try:
        context.user_data['valor'] = float(valor)
        await update.message.reply_text("📋 Categoria do ganho (ex: Salário, Venda, Pix, etc)?")
        return CATEGORIA_GANHO
    except ValueError:
        await update.message.reply_text("❌ Valor inválido, tente novamente.")
        return VALOR_GANHO

async def salvar_categoria_ganho(update, context):
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text("🏦 Conta (nome)?")
    return CONTA_GANHO

async def salvar_conta_ganho(update, context):
    context.user_data['conta'] = update.message.text
    await update.message.reply_text("📅 Data (YYYY-MM-DD)?")
    return DATA_GANHO

async def salvar_data_ganho(update, context):
    context.user_data['data'] = update.message.text
    db = get_db()
    db.ganhos.insert_one({
        'user_id': update.message.from_user.id,
        'valor': context.user_data['valor'],
        'categoria': context.user_data['categoria'],
        'conta': context.user_data['conta'],
        'data': context.user_data['data']
    })
    await update.message.reply_text("✅ Ganho registrado com sucesso! Use /menu para outras ações.")
    return ConversationHandler.END

cadastrar_ganho_handler = ConversationHandler(
    entry_points=[CommandHandler('ganho', iniciar_ganho)],
    states={
        VALOR_GANHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_valor_ganho)],
        CATEGORIA_GANHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_categoria_ganho)],
        CONTA_GANHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_conta_ganho)],
        DATA_GANHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_data_ganho)],
    },
    fallbacks=[]
)

async def listar_ganhos(update, context):
    db = get_db()
    ganhos = list(db.ganhos.find({'user_id': update.message.from_user.id}))
    if not ganhos:
        await update.message.reply_text("📈 Nenhum ganho registrado.")
        return ConversationHandler.END
    msg = "📈 *Seus Ganhos:*\n\n"
    for i, ganho in enumerate(ganhos, 1):
        msg += (f"{i}. {ganho['categoria']}\n"
                f"   💵 R$ {ganho['valor']:.2f} | 🏦 {ganho['conta']} | 📅 {ganho['data']}\n"
                f"   🆔 `{str(ganho['_id'])}`\n\n")
    msg += "\nPara alterar: /alterar_ganho <ID>\nPara excluir: /excluir_ganho <ID>"
    await update.message.reply_text(msg, parse_mode='Markdown')
    return ConversationHandler.END

listar_ganhos_handler = CommandHandler('listar_ganhos', listar_ganhos)

async def iniciar_alteracao_ganho(update, context):
    try:
        ganho_id = context.args[0]
        db = get_db()
        ganho = db.ganhos.find_one({'_id': ObjectId(ganho_id), 'user_id': update.message.from_user.id})
        if not ganho:
            await update.message.reply_text("❌ Ganho não encontrado. Use /listar_ganhos para ver os IDs.")
            return ConversationHandler.END
        context.user_data['ganho_id'] = ganho_id
        await update.message.reply_text(f"Novo valor (atual: {ganho['valor']}):")
        return VALOR_NOVO_G
    except:
        await update.message.reply_text("❌ ID inválido. Use /listar_ganhos para ver os IDs.")
        return ConversationHandler.END

async def salvar_valor_novo_g(update, context):
    try:
        context.user_data['valor'] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("Nova categoria:")
        return CATEGORIA_NOVA_G
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Tente novamente.")
        return VALOR_NOVO_G

async def salvar_categoria_nova_g(update, context):
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text("Nova conta:")
    return CONTA_NOVA_G

async def salvar_conta_nova_g(update, context):
    context.user_data['conta'] = update.message.text
    await update.message.reply_text("Nova data (YYYY-MM-DD):")
    return DATA_NOVA_G

async def salvar_data_nova_g(update, context):
    context.user_data['data'] = update.message.text
    db = get_db()
    db.ganhos.update_one(
        {'_id': ObjectId(context.user_data['ganho_id']), 'user_id': update.message.from_user.id},
        {'$set': {
            'valor': context.user_data['valor'],
            'categoria': context.user_data['categoria'],
            'conta': context.user_data['conta'],
            'data': context.user_data['data']
        }}
    )
    await update.message.reply_text("✅ Ganho alterado com sucesso!")
    return ConversationHandler.END

alterar_ganho_handler = ConversationHandler(
    entry_points=[CommandHandler('alterar_ganho', iniciar_alteracao_ganho)],
    states={
        VALOR_NOVO_G: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_valor_novo_g)],
        CATEGORIA_NOVA_G: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_categoria_nova_g)],
        CONTA_NOVA_G: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_conta_nova_g)],
        DATA_NOVA_G: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_data_nova_g)],
    },
    fallbacks=[]
)

async def excluir_ganho(update, context):
    try:
        ganho_id = context.args[0]
        db = get_db()
        result = db.ganhos.delete_one({'_id': ObjectId(ganho_id), 'user_id': update.message.from_user.id})
        if result.deleted_count > 0:
            await update.message.reply_text("🗑️ Ganho excluído com sucesso!")
        else:
            await update.message.reply_text("❌ Ganho não encontrado ou você não tem permissão.")
    except Exception:
        await update.message.reply_text("❌ ID inválido ou erro na exclusão. Use /listar_ganhos para ver os IDs.")

excluir_ganho_handler = CommandHandler('excluir_ganho', excluir_ganho)

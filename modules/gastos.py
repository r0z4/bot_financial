from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from database import get_db
from bson.objectid import ObjectId

# Estados da conversa
VALOR, CATEGORIA, CONTA, DATA = range(4)
ESCOLHA, VALOR_NOVO, CATEGORIA_NOVA, CONTA_NOVA, DATA_NOVA = range(4, 9)
ESCOLHA_EXCLUIR = 9

# Cadastrar gasto
async def iniciar_cadastro(update, context):
    await update.message.reply_text("💰 Qual o valor do gasto?")
    return VALOR

async def salvar_valor(update, context):
    valor = update.message.text.replace(",", ".")
    try:
        context.user_data['valor'] = float(valor)
        await update.message.reply_text("🏷️ Categoria do gasto?")
        return CATEGORIA
    except ValueError:
        await update.message.reply_text("❌ Valor inválido, tente novamente.")
        return VALOR

async def salvar_categoria(update, context):
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text("🏦 Conta (nome)?")
    return CONTA

async def salvar_conta(update, context):
    context.user_data['conta'] = update.message.text
    await update.message.reply_text("📅 Data (YYYY-MM-DD)?")
    return DATA

async def salvar_data(update, context):
    context.user_data['data'] = update.message.text
    db = get_db()
    db.gastos.insert_one({
        'user_id': update.message.from_user.id,
        'valor': context.user_data['valor'],
        'categoria': context.user_data['categoria'],
        'conta': context.user_data['conta'],
        'data': context.user_data['data']
    })
    await update.message.reply_text("✅ Gasto cadastrado com sucesso! Use /menu para outras ações.")
    return ConversationHandler.END

# Alterar gasto
async def iniciar_alteracao(update, context):
    try:
        gasto_id = context.args[0]
        db = get_db()
        gasto = db.gastos.find_one({'_id': ObjectId(gasto_id), 'user_id': update.message.from_user.id})
        if not gasto:
            await update.message.reply_text("❌ Gasto não encontrado. Use /listar_gastos para ver os IDs.")
            return ConversationHandler.END
        context.user_data['gasto_id'] = gasto_id
        await update.message.reply_text(f"💰 Novo valor (atual: R$ {gasto['valor']}):")
        return VALOR_NOVO
    except:
        await update.message.reply_text("❌ ID inválido. Use /listar_gastos para ver os IDs.")
        return ConversationHandler.END

async def salvar_valor_novo(update, context):
    try:
        context.user_data['valor'] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("🏷️ Nova categoria:")
        return CATEGORIA_NOVA
    except ValueError:
        await update.message.reply_text("❌ Valor inválido, tente novamente.")
        return VALOR_NOVO

async def salvar_categoria_nova(update, context):
    context.user_data['categoria'] = update.message.text
    await update.message.reply_text("🏦 Nova conta:")
    return CONTA_NOVA

async def salvar_conta_nova(update, context):
    context.user_data['conta'] = update.message.text
    await update.message.reply_text("📅 Nova data (YYYY-MM-DD):")
    return DATA_NOVA

async def salvar_data_nova(update, context):
    context.user_data['data'] = update.message.text
    db = get_db()
    db.gastos.update_one(
        {'_id': ObjectId(context.user_data['gasto_id']), 'user_id': update.message.from_user.id},
        {'$set': {
            'valor': context.user_data['valor'],
            'categoria': context.user_data['categoria'],
            'conta': context.user_data['conta'],
            'data': context.user_data['data']
        }}
    )
    await update.message.reply_text("✅ Gasto alterado com sucesso!")
    return ConversationHandler.END

# Listar gastos
async def listar_gastos(update, context):
    db = get_db()
    gastos = list(db.gastos.find({'user_id': update.message.from_user.id}))
    if not gastos:
        await update.message.reply_text(
            "📋 *Seus Gastos*\n\n"
            "⚠️ Nenhum gasto encontrado.\n"
            "Cadastre seu primeiro gasto com /gasto!",
            parse_mode='Markdown'
        )
        return
    
    msg = "📋 *Seus Gastos:*\n\n"
    for i, gasto in enumerate(gastos, 1):
        msg += (f"{i}. 🏷️ {gasto['categoria']}\n"
               f"   💰 R$ {gasto['valor']:.2f} | 🏦 {gasto['conta']} | 📅 {gasto['data']}\n"
               f"   🆔 `{str(gasto['_id'])}`\n\n")
    
    msg += ("💡 *Para gerenciar:*\n"
           "• `/alterar_gasto <ID>` - Alterar\n"
           "• `/excluir_gasto <ID>` - Excluir")
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# Excluir gasto
async def excluir_gasto(update, context):
    try:
        gasto_id = context.args[0]
        db = get_db()
        result = db.gastos.delete_one({'_id': ObjectId(gasto_id), 'user_id': update.message.from_user.id})
        if result.deleted_count > 0:
            await update.message.reply_text("🗑️ Gasto excluído com sucesso!")
        else:
            await update.message.reply_text("❌ Gasto não encontrado ou você não tem permissão.")
    except Exception as e:
        await update.message.reply_text("❌ ID inválido ou erro na exclusão. Use /listar_gastos para ver os IDs.")

# Handlers
cadastrar_gasto_handler = ConversationHandler(
    entry_points=[CommandHandler('gasto', iniciar_cadastro)],
    states={
        VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_valor)],
        CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_categoria)],
        CONTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_conta)],
        DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_data)],
    },
    fallbacks=[]
)

alterar_gasto_handler = ConversationHandler(
    entry_points=[CommandHandler('alterar_gasto', iniciar_alteracao)],
    states={
        VALOR_NOVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_valor_novo)],
        CATEGORIA_NOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_categoria_nova)],
        CONTA_NOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_conta_nova)],
        DATA_NOVA: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_data_nova)],
    },
    fallbacks=[]
)

listar_gastos_handler = CommandHandler('listar_gastos', listar_gastos)
excluir_gasto_handler = CommandHandler('excluir_gasto', excluir_gasto)

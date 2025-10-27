from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters
from database import get_db
from datetime import datetime

# Saldos em memória (para cada user_id)
SET_SALDO, EDITAR_SALDO = range(2)
saldo_inicial = {}

# /saldo_inicial
async def pedir_saldo_inicial(update, context):
    await update.message.reply_text("Informe o saldo inicial (apenas números, ex: 500):")
    return SET_SALDO

async def salvar_saldo_inicial(update, context):
    user_id = update.message.from_user.id
    try:
        valor = float(update.message.text.replace(",", "."))
        saldo_inicial[user_id] = valor
        await update.message.reply_text(f"Saldo inicial definido: R$ {valor:.2f}")
    except:
        await update.message.reply_text("Valor inválido. Tente novamente com apenas números (ex: 550,80)")
        return SET_SALDO
    return ConversationHandler.END

set_saldo_inicial_handler = ConversationHandler(
    entry_points=[CommandHandler('saldo_inicial', pedir_saldo_inicial)],
    states={SET_SALDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_saldo_inicial)]},
    fallbacks=[]
)

# /editar_saldo
async def pedir_novo_saldo(update, context):
    await update.message.reply_text("Qual o novo saldo inicial? (apenas números)")
    return EDITAR_SALDO

async def salvar_novo_saldo(update, context):
    user_id = update.message.from_user.id
    try:
        valor = float(update.message.text.replace(",", "."))
        saldo_inicial[user_id] = valor
        await update.message.reply_text(f"Saldo inicial atualizado para R$ {valor:.2f}")
    except:
        await update.message.reply_text("Valor inválido! Envie só o número.")
        return EDITAR_SALDO
    return ConversationHandler.END

editar_saldo_inicial_handler = ConversationHandler(
    entry_points=[CommandHandler('editar_saldo', pedir_novo_saldo)],
    states={EDITAR_SALDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_novo_saldo)]},
    fallbacks=[]
)

# /excluir_saldo
async def excluir_saldo_inicial(update, context):
    user_id = update.message.from_user.id
    if user_id in saldo_inicial:
        del saldo_inicial[user_id]
        await update.message.reply_text("Saldo inicial excluído.")
    else:
        await update.message.reply_text("Você não possui saldo inicial registrado.")

excluir_saldo_inicial_handler = CommandHandler('excluir_saldo', excluir_saldo_inicial)

# /extrato
async def consultar_extrato(update, context):
    db = get_db()
    user_id = update.message.from_user.id

    ganhos = list(db.ganhos.find({"user_id": user_id}))
    gastos = list(db.gastos.find({"user_id": user_id}))
    movimentos = []
    
    for g in ganhos:
        movimentos.append({
            "tipo": "ganho",
            "valor": float(g['valor']),
            "categoria": g['categoria'],
            "conta": g['conta'],
             "data": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    for g in gastos:
        movimentos.append({
            "tipo": "gasto",
            "valor": float(g['valor']),
            "categoria": g['categoria'],
            "conta": g['conta'],
             "data": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    movimentos.sort(key=lambda x: x['data'])

    saldo = saldo_inicial.get(user_id, 0.0)
    extrato = "💳 *Extrato de Movimentações*\n\n"

    if not movimentos:
        if user_id in saldo_inicial:
            extrato += f"Você não lançou nenhum ganho ou gasto.\n\nSaldo inicial atual: R$ {saldo:.2f}"
        else:
            extrato += "Nenhum movimento encontrado.\nCadastre seu primeiro ganho ou gasto!"
        await update.message.reply_text(extrato, parse_mode="Markdown")
        return

    for m in movimentos:
        saldo_antes = saldo
        if m["tipo"] == "ganho":
            saldo += m["valor"]
            sinal = "+"
            emoji = "🟢"
        else:
            saldo -= m["valor"]
            sinal = "-"
            emoji = "🔴"
        extrato += (
            f"{emoji} {m['data']} | {m['categoria']} ({m['conta']})\n"
            f"    {sinal} R$ {m['valor']:.2f}\n"
            f"    Saldo antes: R$ {saldo_antes:.2f} → Saldo depois: R$ {saldo:.2f}\n"
        )
    extrato += f"\n🏁 *Saldo final*: R$ {saldo:.2f}"
    await update.message.reply_text(extrato, parse_mode="Markdown")

consultar_extrato_handler = CommandHandler('extrato', consultar_extrato)

# /extrato_periodo
async def extrato_periodo(update, context):
    db = get_db()
    user_id = update.message.from_user.id
    try:
        data_ini = context.args[0]
        data_fim = context.args[1]
    except:
        await update.message.reply_text("Envie assim: /extrato_periodo <data_inicio> <data_fim> (YYYY-MM-DD)")
        return

    ganhos = list(db.ganhos.find({"user_id": user_id, "data": {"$gte": data_ini, "$lte": data_fim}}))
    gastos = list(db.gastos.find({"user_id": user_id, "data": {"$gte": data_ini, "$lte": data_fim}}))
    total_ganhos = sum(float(g['valor']) for g in ganhos)
    total_gastos = sum(float(g['valor']) for g in gastos)
    saldo = total_ganhos - total_gastos

    resposta = (
        f"📅 *Extrato de {data_ini} a {data_fim}:*\n\n"
        f"🟢 Ganhos: R$ {total_ganhos:.2f}\n"
        f"🔴 Gastos: R$ {total_gastos:.2f}\n"
        f"💰 *Saldo:* R$ {saldo:.2f}"
    )
    await update.message.reply_text(resposta, parse_mode='Markdown')

extrato_periodo_handler = CommandHandler('extrato_periodo', extrato_periodo)

# /estatisticas
async def estatisticas(update, context):
    db = get_db()
    user_id = update.message.from_user.id

    ganhos = list(db.ganhos.find({"user_id": user_id}))
    gastos = list(db.gastos.find({"user_id": user_id}))

    categorias_ganhos = {}
    categorias_gastos = {}

    for g in ganhos:
        cat = g['categoria']
        val = float(g['valor'])
        categorias_ganhos[cat] = categorias_ganhos.get(cat, 0) + val

    for g in gastos:
        cat = g['categoria']
        val = float(g['valor'])
        categorias_gastos[cat] = categorias_gastos.get(cat, 0) + val

    resposta = "📊 Estatísticas por categoria:\n\n"
    resposta += "🟢 Ganhos:\n"
    for cat, val in categorias_ganhos.items():
        resposta += f"  - {cat}: R$ {val:.2f}\n"

    resposta += "\n🔴 Gastos:\n"
    for cat, val in categorias_gastos.items():
        resposta += f"  - {cat}: R$ {val:.2f}\n"

    await update.message.reply_text(resposta)

estatisticas_handler = CommandHandler('estatisticas', estatisticas)

import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from modules.especie import (
    especie_handler,
    saldo_especie_handler,
    editar_especie_handler,
    excluir_especie_handler,
    listar_especie_handler)
from modules.metas import metas_handler, listar_metas_handler
from modules.gastos import (
    cadastrar_gasto_handler,
    listar_gastos_handler,
    excluir_gasto_handler,
    alterar_gasto_handler
)
from modules.ganhos import (
    cadastrar_ganho_handler,
    listar_ganhos_handler,
    alterar_ganho_handler,
    excluir_ganho_handler
)
from modules.extrato import (
    consultar_extrato_handler,
    extrato_periodo_handler,
    estatisticas_handler,
    set_saldo_inicial_handler,
    editar_saldo_inicial_handler,
    excluir_saldo_inicial_handler
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Deve estar como TELEGRAM_TOKEN no .env

print(f"Token fornecido: {TOKEN}")

async def start(update, context):
    await update.message.reply_text("Bem-vindo ao seu bot financeiro! Use /menu para começar.")

async def menu(update, context):
    await update.message.reply_text(
        "Menu:\n"
        "/gasto - Cadastrar gasto\n"
        "/ganho - Cadastrar ganho\n"
        "/extrato - Ver extrato\n"
        "/extrato_periodo - Ver extrato por período\n"
        "/estatisticas - Ver estatísticas\n"
        "/saldo_inicial - Definir saldo inicial\n"
        "/listar_ganhos - Listar ganhos\n"
        "/listar_gastos - Listar gastos\n"
        "/especie - Dinheiro em espécie\n"
        "/meta - Gerenciar metas\n"
        "/conta - Gerenciar contas bancárias"
    )

def main():
    application = Application.builder().token(TOKEN).build()
    # Básicos do bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    # Gastos
    application.add_handler(cadastrar_gasto_handler)
    application.add_handler(listar_gastos_handler)
    application.add_handler(alterar_gasto_handler)
    application.add_handler(excluir_gasto_handler)
    # Ganhos
    application.add_handler(cadastrar_ganho_handler)
    application.add_handler(listar_ganhos_handler)
    application.add_handler(alterar_ganho_handler)
    application.add_handler(excluir_ganho_handler)
    # Outros
    application.add_handler(consultar_extrato_handler)
    application.add_handler(extrato_periodo_handler)
    application.add_handler(estatisticas_handler)
    application.add_handler(set_saldo_inicial_handler)
    application.add_handler(editar_saldo_inicial_handler)
    application.add_handler(excluir_saldo_inicial_handler)
    application.add_handler(especie_handler)
    application.add_handler(saldo_especie_handler)
    application.add_handler(editar_especie_handler)
    application.add_handler(excluir_especie_handler)
    application.add_handler(listar_especie_handler)
    application.add_handler(metas_handler)
    application.add_handler(listar_metas_handler)
    # application.add_handler(especie_handlers)
    # application.add_handler(metas_handlers)
    # application.add_handler(bancos_handler)
    application.run_polling()

if __name__ == "__main__":
    main()

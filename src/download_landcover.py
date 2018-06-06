from pymodis import downmodis
import os

"""-------------------------------------------------------------
    ROTINA: Download dos arquivos de LC (Cobertura de Solo)
-------------------------------------------------------------"""
# Configura a localização absoluta dos diretórios de trabalho
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR,'data')

# Configuração do período temporal da análise
# Para ilustração em sala, será usado apenas o mês 09/2003
mes_inicio  = 1
ano_inicio  = 2003
mes_final   = 12
ano_final   = 2012

# Parâmetros para download do dado do MODIS
# Cena que contêm o município de Fortaleza
tiles = "h14v09"
# Lista com o produto, o satelite e a pasta onde está localizado os arquivos no ftp
produto = "MCD12Q1.006"
pasta = "MOTA"
# Faz a leitura do login e senha armazenado em um arquivo
with open("data/login_senha.txt") as f:
    info = f.readlines()
f.close()
# Armazena as informações de usuario e senha
usuario = info[0][:-1]
senha = info[1][:-1]

# Faz o download
for year in range(ano_inicio, ano_final + 1):
    for month in range(mes_inicio, mes_final + 1):
        dia_final   = "%04d.12.31" % (year)
        dia_inicial = "%04d.01.01" % (year)

        # Cria o diretório para armazenar as imagens
        destino = os.path.join(BASE_DIR,"data/landcover")

        if not os.path.isdir(destino):
            os.makedirs(destino)

        # Cria uma classe de download do MODIS, conecta e faz o download
        modis_down = downmodis.downModis(password=senha, user=usuario, destinationFolder=destino, path=pasta,\
                                         tiles=tiles, today=dia_final, enddate=dia_inicial, product=produto)
        modis_down.connect()
        modis_down.downloadsAllDay()
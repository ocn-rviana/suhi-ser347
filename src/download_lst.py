from pymodis import downmodis
import calendar
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

# Configuração dos satélites
satelite = ["terra", "aqua"]
# Período da análise
periodo  = ["day" , "night"]
# Parâmetros para download do dado do MODIS
# Cena que contêm o município de Fortaleza
tiles = "h14v09"
# Lista com o produto, o satelite e a pasta onde está localizado os arquivos no ftp
produto = ["MOD11A2.006","MYD11A2.006"]
pasta = ['MOLT','MOLA']
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
        for i in range(0, 2):
            dia_final   = "%04d.%02d.%02d" % (year, month, calendar.monthrange(year, month)[1])
            dia_inicial = "%04d.%02d.01" % (year, month)

            # Cria o diretório para armazenar as imagens
            destino = os.path.join(BASE_DIR,"data/lst/%s/%04d/%02d" % (satelite[i],year,month))

            if not os.path.isdir(destino):
                os.makedirs(destino)

            # Cria uma classe de download do MODIS, conecta e faz o download
            modis_down = downmodis.downModis(password=senha, user=usuario, destinationFolder=destino, path=pasta[i], tiles=tiles, today=dia_final, enddate=dia_inicial, product=produto[i])
            modis_down.connect()
            modis_down.downloadsAllDay()
"""-------------------------------------------------------------
    IMPORTAÇÃO DE BIBLIOTECAS
-------------------------------------------------------------"""
# Bibliotecas OS
import os
import calendar

# Bibliotecas Numéricas
import numpy as np
import pandas as pd
from collections import OrderedDict
from scipy.ndimage import zoom

# Bibliotecas Geográficas
from osgeo import gdal
from pyproj import Proj, transform
import fiona

# Bibliotecas Gráficas
import matplotlib.pyplot as plt
from descartes import PolygonPatch

# Irfoma o uso de exceções
gdal.UseExceptions()

"""-------------------------------------------------------------
    DEFINIÇÃO DE FUNÇÕES PRÓPRIAS
-------------------------------------------------------------"""
# Conversão de valores binários para valores decimais
def count_days(bin_array):
    shp_array = bin_array.shape
    row = shp_array[0]
    col = shp_array[1]

    int_array = np.zeros((row,col))

    for r in range(row):
        for c in range(col):
            clear_days = bin(bin_array[r,c])
            days = clear_days[2:].count('1')
            int_array[r,c] = days

    return int_array

# Normalização dos dados
def nrs_scale(original_lst, k):
    # Constroi o denominador
    square = original_lst ** 2
    sum_square = np.nansum(square)
    new_lst = original_lst / (sum_square ** 0.5)

    if k == 0:
        N = 25300 # Valor apropriado de temperatura para o dia
    else:
        N = 24100 # Valor apropriado de temperatura para a noite

    output_lst = N * new_lst

    return output_lst

# Calculo do índice segundo Jin
def suhi_index(lst_array, lc_array):
    index_urban = lc_array == 13
    mean_lst_urban = np.nanmean(lst_array[index_urban])

    lc_types = [x for x in range(1,18)]
    lc_types.remove(13)

    suhi_value= []

    for lc in lc_types:
        index_urban = lc_array == lc
        mean_lst_lc = np.nanmean(lst_array[index_urban])
        suhi = mean_lst_urban - mean_lst_lc
        suhi_value.append(suhi)

    return suhi_value

"""-------------------------------------------------------------
    CONFIGURAÇÃO DOS DIRETÓRIOS DE TRABALHO
-------------------------------------------------------------"""
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR,'data')
IMGS_DIR = os.path.join(BASE_DIR,'imgs')

"""-------------------------------------------------------------
    CONFIGURAÇÃO DOS RECORTES ESPAÇO/TEMPORAIS
-------------------------------------------------------------"""
# Configuração do período temporal da análise
ano_inicio  = 2003
ano_final   = 2012
mes_inicio  = 1
mes_final   = 12

# Configuração do recorte espacial da análise
lat_max = -3.6
lat_min = lat_max - 0.4
lon_min = -38.75
lon_max = lon_min + 0.4

"""-------------------------------------------------------------
    RECORTE DO SHAPEFILE DE FORTALEZA
-------------------------------------------------------------"""
with fiona.open("data/shapes/Ceara_Municipios.shp", "r") as shapefile:
    # Número de feições
    for feature in shapefile:
        if feature['properties']['NOMEMUNI'] == "FORTALEZA":
            f = feature['geometry']

"""-------------------------------------------------------------
    CONFIGURAÇÃO DAS ANALISES A SEREM REALIZADAS
-------------------------------------------------------------"""
# Configuração dos satélites
satelite = ["aqua", "terra"]
periodo  = ["day" , "night"]

# # Determina quais plots serão feitos:
landcover_plot = True
landcover_hist = True
lst_plot       = True
clear_plot     = True
suhi_plot      = True

"""-------------------------------------------------------------
    INICIALIZAÇÃO DE DATAFRAME PARA SUHI
-------------------------------------------------------------"""
DICT = {'YEAR':[], 'MONTH':[], 'DAY':[], 'SATELLITE':[], 'PERIOD':[],
        'LC_1':[], 'LC_2':[], 'LC_3':[], 'LC_4':[], 'LC_5':[], 'LC_6':[],
        'LC_7':[], 'LC_8':[], 'LC_9':[], 'LC_10':[], 'LC_11':[],
        'LC_12':[], 'LC_14':[], 'LC_15':[], 'LC_16':[], 'LC_17':[],
    }

SUHI = pd.DataFrame(OrderedDict(DICT))
index_df = 0

"""-------------------------------------------------------------
    PROGRAMA PRINCIPAL
-------------------------------------------------------------"""
# Lê os arquivos de Cobertura de Solo e os organiza por lista
MODIS_LC_FILES = os.listdir(path=os.path.join(DATA_DIR, 'landcover'))
MODIS_LC_FILES.sort()

# Procedimento para remover os arquivos que acompanharam os dados hdf de cobertura de solo
COUNT_FILE = MODIS_LC_FILES.copy()
for file in COUNT_FILE:
    if file[-3:] != "hdf":
        MODIS_LC_FILES.remove(file)

for file in MODIS_LC_FILES:
    year = int(file[9:13])

    # Realiza a leitura da Cobertura de Solo
    lc_fname = os.path.join(DATA_DIR, 'landcover', file)

    # Abertura do raster de Cobertura do Solo
    lc_raster = gdal.Open(gdal.Open(lc_fname, gdal.GA_ReadOnly).GetSubDatasets()[0][0], gdal.GA_ReadOnly)
    # Obtẽm os valores numéricos do raster
    lc_values = lc_raster.GetRasterBand(1).ReadAsArray()

    # Adquirindo as informações geográficas
    geo_lc = lc_raster.GetGeoTransform()
    latitude = geo_lc[3]        # latitude do canto superior esquerda
    longitude = geo_lc[0]       # longitude do canto superior esquerda
    resolucao = geo_lc[1]       # resolução do pixel

    # Inicializa matrizes para armazerar as coordenadas sinusiodais
    lon_sin = np.zeros((lc_raster.RasterXSize, lc_raster.RasterYSize))
    lat_sin = np.zeros((lc_raster.RasterXSize, lc_raster.RasterYSize))

    # Preenche a matriz com as coordenadas na projeção sinusiodal
    for row in range(lc_raster.RasterYSize):
        for col in range(lc_raster.RasterXSize):
            lon_sin[row, col] = longitude + col * resolucao
            lat_sin[row, col] = latitude - row * resolucao

    # Realiza a transformação das coordenadas de sinusiodal --> wgs84
    sinu = Proj("+proj=sinu +R=6371007.181 +nadgrids=@null +wktext")
    wgs84 = Proj("+init=EPSG:4326")
    lon_wgs,lat_wgs = transform(sinu,wgs84,lon_sin,lat_sin)

    # Realiza um recorte nos dados de acordo com a latitude e longitude informada
    ind = np.asarray(np.where((lat_wgs >= lat_min)
                              & (lat_wgs <= lat_max)
                              & (lon_wgs >= lon_min)
                              & (lon_wgs <= lon_max)))
    # Identifica os valores de max e min nas linhas e colunas, necessário para a criação da sub-matriz
    row_min = np.amin(ind[0, :])
    row_max = np.amax(ind[0, :]) + 1
    col_min = np.amin(ind[1, :])
    col_max = np.amax(ind[1, :]) + 1

    indices = (row_min, row_max, col_min, col_max)

    crop_lat_lc    = np.array(lat_wgs[row_min:row_max, col_min:col_max])
    crop_lon_lc    = np.array(lon_wgs[row_min:row_max, col_min:col_max])
    crop_values_lc = np.array(lc_values[row_min:row_max, col_min:col_max])

    if landcover_plot:
        # Cria diretórios para armazenar a figura
        fig_dir = os.path.join(IMGS_DIR, 'landcover')
        fig_fname = os.path.join(fig_dir, 'landcover_{}'.format(year))

        if not os.path.isdir(fig_dir):
            os.makedirs(fig_dir)

        # Define um colormap discretizado
        cmap = plt.get_cmap('terrain_r', 17)
        # Extrai todas as cores do colormap para uma lista
        cmaplist = [cmap(i) for i in range(cmap.N)]
        # Força a entrada (12, área urbana) a ser vermelha
        cmaplist[12] = (1.0, 0.0, 0.0, 1.0)
        # Cria um novo cmap
        cmap = cmap.from_list('Colormap customizado', cmaplist, cmap.N)

        fig = plt.figure(figsize=(13, 10))
        ax = fig.add_subplot(111)
        plt.pcolormesh(crop_lon_lc, crop_lat_lc, crop_values_lc, cmap=cmap, vmin=0.5, vmax=17 + 0.5)
        plt.colorbar(ticks=np.arange(1, 18))
        plt.title("Cobertura de Solo de Fortaleza - {}".format(year), fontsize=18)
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.ylim(lat_min, lat_max)
        plt.xlim(lon_min, lon_max)
        ax.add_patch(PolygonPatch(f, facecolor="none", edgecolor='k', linewidth=2))
        plt.savefig(fig_fname, bbox_inches='tight')
        plt.close()

    # Obtêm um histograma com os valores de cobertura de solo
    lc_types = range(1,18)
    # Inicializa uma lista pra armazenar o número de pixels do tipo de cobertura
    lc_hist = []

    for value in lc_types:
        lc_total = (crop_values_lc == value).sum()
        lc_hist.append(lc_total)

    # Obtêm o total de pixels na cena
    lc_pixels = sum(lc_hist)
    # Calcula o percentual de pixels para cada tipo de cobertura
    lc_phist = [(x * 100) / lc_pixels for x in lc_hist]

    if landcover_hist:
        fig_name = os.path.join(fig_dir, 'landcover_{}_hist'.format(year))

        ## Plota o histograma com os dados
        fig = plt.figure(figsize=(12, 6))
        plt.bar(lc_types, lc_phist)
        plt.title("Histograma da Cobertura de Solo de Fortaleza - {}".format(year), fontsize=16)
        plt.ylim(0, 50)
        plt.xlim(0, 18)
        plt.xticks(np.arange(1, 18, 1))
        plt.xlabel("Tipo de Cobertura")
        plt.ylabel("Percentual (%)")
        plt.savefig(fig_name, bbox_inches='tight')
        plt.close()

    # Analise de LST
    # Primeiro por satellite
    for sat in satelite:
        # Depois por periodo
        for k in [0,1]:
            # Indice do SubDataSet do MODIS LST para dia e noite
            isds = int((5**k) - 1)
            for mes in range(mes_inicio, mes_final + 1):
                line = [year, mes, 15, sat, periodo[k]]

                # Define o diretorio onde se encontra os dados de LST
                LST_DIR = os.path.join(DATA_DIR,"lst/%s/%04d/%02d" % (sat,year,mes))

                # Faz a leitura dos arquivos para cada mês
                MODIS_LST_FILES = os.listdir(LST_DIR)
                MODIS_LST_FILES.sort()
                COUNT_FILE = MODIS_LST_FILES.copy()

                for file in COUNT_FILE:
                    if file[-3:] != "hdf":
                        MODIS_LST_FILES.remove(file)

                # Cria uma lista para armazenar os valores de LST no mês
                lst_record   = []
                clear_record = []

                for fname in MODIS_LST_FILES:
                    # Armazena o nome do arquivo de LST
                    lst_fname = os.path.join(LST_DIR, fname)
                    print(lst_fname)

                    # AQUISIÇÃO DE LST
                    lst_raster = gdal.Open(gdal.Open(lst_fname, gdal.GA_ReadOnly).GetSubDatasets()[isds][0],
                                           gdal.GA_ReadOnly)
                    lst_values = lst_raster.GetRasterBand(1).ReadAsArray() * 0.02
                    lst_values[lst_values == 0] = np.NaN

                    lst_record.append(lst_values)

                    # AQUISIÇÃO DE DIAS EM CONDIÇÕES CLARAS
                    clear_raster = gdal.Open(gdal.Open(lst_fname, gdal.GA_ReadOnly).GetSubDatasets()[10 + k][0],
                                             gdal.GA_ReadOnly)
                    clear_values = clear_raster.GetRasterBand(1).ReadAsArray()
                    clear_days   = count_days(clear_values)

                    clear_record.append(clear_days)

                # Converte a lista em um array e faz a media das cenas
                record = np.array(lst_record)
                lst_mean = np.nanmean(record, axis=0)

                # Contagem dos dias claros no mes
                record = np.array(clear_record)
                lst_clear = record.sum(axis=0)
                lst_clear[lst_clear == 0] = np.NaN

                # Reamostra a média para a resolução da landcover
                lst_mean_resample  = zoom(lst_mean, zoom=2.0, order=0)
                lst_clear_resample = zoom(lst_clear, zoom=2.0, order=0)

                # Recorta a cena para a area de estudo, com base nas coordenadas de landcover
                crop_values_lst = np.array(lst_mean_resample[row_min:row_max, col_min:col_max])
                crop_values_clear = np.array(lst_clear_resample[row_min:row_max, col_min:col_max])

                crop_nrs_lst = nrs_scale(crop_values_lst, k)

                if lst_plot:
                    # Gera diretórios para armazenar a figura
                    fig_dir = os.path.join(IMGS_DIR, "lst/%s/%s/%04d" % (sat,periodo[k],year))
                    fig_name = os.path.join(fig_dir, '{}.png'.format(mes))

                    if not os.path.isdir(fig_dir):
                        os.makedirs(fig_dir)

                    if k == 0:
                        vmin = 300;
                        vmax = 315
                    else:
                        vmin = 290;
                        vmax = 300

                    fig = plt.figure(figsize=(16, 6))
                    ax = fig.add_subplot(121)
                    plt.pcolormesh(crop_lon_lc, crop_lat_lc, crop_values_lst, cmap='RdBu_r', vmin=vmin, vmax=vmax)
                    plt.ylim(lat_min, lat_max)
                    plt.xlim(lon_min, lon_max)
                    plt.title("LST original de Fortaleza - {}/{}".format(mes, year), fontsize=14)
                    plt.xlabel("Longitude")
                    plt.ylabel("Latitude")
                    ax.add_patch(PolygonPatch(f, facecolor="none", edgecolor='k', linewidth=2))
                    plt.colorbar()
                    # plt.savefig(fig_name, bbox_inches='tight')

                    ax = fig.add_subplot(122)
                    plt.pcolormesh(crop_lon_lc, crop_lat_lc, crop_nrs_lst, cmap='RdBu_r', vmin=vmin, vmax=vmax)
                    plt.ylim(lat_min, lat_max)
                    plt.xlim(lon_min, lon_max)
                    plt.title("$LST_{NRS}$ normalizada de Fortaleza - %d/%d" % (mes, year), fontsize=14)
                    plt.xlabel("Longitude")
                    plt.ylabel("Latitude")
                    ax.add_patch(PolygonPatch(f, facecolor="none", edgecolor='k', linewidth=2))
                    plt.colorbar()
                    plt.savefig(fig_name, bbox_inches='tight')
                    plt.close()

                # Obtêm o número de dias no mês
                dias_do_mes = calendar.monthrange(year,mes)[1]

                if clear_plot:
                    # Gera diretórios para armazenar a figura
                    fig_dir = os.path.join(IMGS_DIR, "lst/%s/%s/%04d" % (sat, periodo[k], year))
                    fig_name = os.path.join(fig_dir, '{}_clear_days.png'.format(mes))

                    if not os.path.isdir(fig_dir):
                        os.makedirs(fig_dir)

                    # get discrete colormap
                    cmap = plt.get_cmap('gray', dias_do_mes)

                    fig = plt.figure(figsize=(11, 8))
                    ax = fig.add_subplot(111)
                    plt.pcolormesh(crop_lon_lc, crop_lat_lc, crop_values_clear, cmap=cmap, vmin=0.5,
                                   vmax=dias_do_mes + 0.5)
                    plt.colorbar(ticks=np.arange(0, dias_do_mes + 1))
                    plt.ylim(lat_min, lat_max)
                    plt.xlim(lon_min, lon_max)
                    plt.title("Dias com Céu Claro em Fortaleza - %d/%d" % (mes, year), fontsize=14)
                    plt.xlabel("Longitude")
                    plt.ylabel("Latitude")
                    ax.add_patch(PolygonPatch(f, facecolor="none", edgecolor='k', linewidth=2))
                    plt.savefig(fig_name, bbox_inches='tight')
                    plt.close()

                # Obtêm os valores de SUHI para o mês
                suhi_value = suhi_index(crop_nrs_lst, crop_values_lc)

                for value in suhi_value:
                    line.append(value)

                SUHI.loc[index_df] = line
                index_df += 1


SUHI['DATE'] = pd.to_datetime(SUHI[['YEAR','MONTH','DAY']])
SUHI.to_csv('data/suhi.csv', index=False, na_rep = 'NaN')

SUHI.set_index('DATE', inplace=True)

fig_name = os.path.join(IMGS_DIR, 'suhi.png')

fig = plt.figure(figsize=(13, 6))
SUHI.groupby(['PERIOD','SATELLITE'])['LC_9'].plot(legend=True)
plt.title("Variação Temporal do $UHI_{skin}$ no período de %d-%d em Fortaleza/CE" % (ano_inicio, ano_final), fontsize=14)
plt.xlabel("Dias")
plt.ylabel("$UHI_{skin}$ (K)")
plt.savefig(fig_name, bbox_inches='tight')
plt.legend(['Aqua/day', 'Aqua/night', 'Terra/day', 'Terra/night'])


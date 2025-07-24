#!pip install openai
#!pip install unidecode
from openai import OpenAI
import pandas as pd
import os
import numpy as np
import math
from unidecode import unidecode
import re
from tqdm.notebook import tqdm
import json


def get_subdirectories(path):
    subdirectories = [path+'/'+name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
    return subdirectories
    
def get_md_file(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            return filename
    return None

def get_l_art(path = "C:/Users/User/OpenGenesBenchmark/papers/MD_pdf"):
    sd = get_subdirectories(path)
    l_art=[]
    for i in range(len(sd)):
         md = get_md_file(sd[i])
         l_art.append(sd[i]+'/'+md)
    return l_art   

def check_genes(articles, genes):
    print('Find genes in articles')
    results = np.full((len(articles), len(genes)), False, dtype='bool')
    for a in tqdm(range(len(articles))):
        file_data = open(articles[a], 'rb').read()
        for g in range(len(genes)):
            #print(genes[g])
            match = re.findall(genes[g], str(file_data))  
            if match!=[]:
                #print(a,g,match)
                results[a,g] = True
    return results

def get_unique(data_names):
    unique = []
    for a in data_names:
        if not a in unique:
            unique.append(a)
    return unique
    
def prepare_list_genes(df):
    lg = df['hgnc'].tolist()
    ug = get_unique(lg)
    return ug

def filter_list(l):
    ll=[]
    for i in range(len(l)):
        if isinstance(l[i], str):
             ll.append(l[i])
    return ll        

#ген-набор статей где он встречается
def make_list_articles(genes, articles, r):
    #print(len(genes))
    lg=[]
    la=[]
    for i in range(len(genes)):
        laa=[]
        #print(np.sum(r[:,i]))
        if np.sum(r[:,i])>1:
            #print(genes[i])
            lg.append(genes[i])
            for j in range(len(articles)):
                if r[j,i]==True:
                    #print(articles[j])
                    laa.append(articles[j])
            la.append(laa)         
    return lg, la

def check_importance(gene, l, thr=4):
    req = prepare_request_nart(gene, l)
    resp = send_request(req, temperature=0)
    print("resp:",resp)
    v = convert_to_number(resp) 
    if v>=thr:
        return True
    else:
        return False
    
#гены-набор статей где они встречаются
def make_list_genes_articles(genes, articles, r):
    print('Make list importance genes')
    #ma = np.sum(r[:,0]&r[:,1]);ii=0;jj=1
    lg_pair = [];la_pair = []
    for i in tqdm(range(len(genes))):
        for j in range(i+1,len(genes)):
            ma=np.sum(r[:,j]&r[:,i])
            if ma>1:
                print("ma:",ma)
                la =[]
                for a in range(len(articles)):
                    if r[a, i]==True:
                        la.append(articles[a])   
                f1 = check_importance(genes[i], la, thr=4)
                f2 = check_importance(genes[j], la, thr=4)
                if f1 and f2:    
                    lg_pair.append([genes[i],genes[j]])
                    la_pair.append(la)      
    return lg_pair, la_pair


def prepare_request_nart(g, la, long=False):
    s = "Ген " + g + " изучался в " + str(len(la)) + " статьях:\n"
    for a in range(len(la)):
        s = s + "Статья " + str(a+1) + ":"
        #articles = la[a]
        file_data = open(la[a], 'rb').read()
        s=s+ str(file_data) + "\n"  
    s = s + " На основе этих публикаций предскажи, к какому уровню уверенности"
    s = s + "(Highest,High,Моderate,Low,Lowest) должен быть отнесён этот ген в базе OpenGenes? "  
    if long==False:
        s = s + "В ответе приведи только одну оценку только для этого гена."     
    return s

def prepare_request(g, art, long=False):
    s = "Ген " + g + " изучался в данной статье:\n"
    file_data = open(art, 'rb').read()
    s=s + str(file_data) + "\n"  
    s = s + " На основе этой публикации предскажи, к какому уровню уверенности"
    s = s + "(Highest,High,Моderate,Low,Lowest) должен быть отнесён этот ген в базе OpenGenes? "  
    if long==False:
        s = s + "В ответе приведи только одну оценку только для этого гена."     
    return s

def prepare_request_cross(g, la, long=False):
    s = "Ряд генов изучался в нескольких статьях:\n"
    for a in range(len(la)):
        s = s + "Статья " + str(a+1) + ":"
        file_data = open(la[a], 'rb').read()
        s=s+ str(file_data) + "\n"  
    s = s + " Какие гены были важны в данных исследованиях? Напиши только два гена"
    #s = s + " Какие гены были общие в данных исследованиях? Напиши только два гена"
    #if long==False:
    #    s = s + "В ответе приведи только один ген"     
    return s


def convert_to_number(level, default=0):
    chk_str = unidecode(level)
    levels = ["Lowest", "Low", "Moderate", "High", "Highest"]
    levels1 = ["Ловест", "Лов", "Модерат", "Хай", "Хаест"]
    for i in range(len(levels)):
        if levels[i] in chk_str:
            default = i+1
            #break
        if levels1[i] in chk_str:
            default = i+1
            #break  
        if levels[0] in chk_str:
            default = 1
        if levels1[0] in chk_str:
            default = 1            
    return default


def send_request(req, temperature=0.5,max_tokens=75):
    client = OpenAI(
        base_url="http://80.209.242.40:8000/v1",
        api_key="dummy-key"
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-instruct",
            temperature=temperature,
            max_tokens=max_tokens,   #2048
            messages=[
                {"role": "user", "content": req}
            ]
        )  
    except Exception as e:
        return " "
    return response.choices[0].message.content


def save_lists(list1, list2, filename):
    #Сохраняет два списка в файл в формате JSON.
    data = {
        'list1': list1,
        'list2': list2
    }
    with open(filename, 'w') as f:
        json.dump(data, f)

def read_lists(filename):
    #Считывает два списка из файла в формате JSON.
    with open(filename, 'r') as f:
        data = json.load(f)
    return data['list1'], data['list2']


# отклонение средней оценки каждой статьи от оценки всех статей
# суммарно по всем генам
def calc_metric_dev(articles, genes):
    gm = check_genes(articles, genes)
    lg, la = make_list_articles(genes, articles, gm)
    print('Генов в нескольких статьях:', len(lg))
    print(lg)
    gmetrics=[]
    for i in tqdm(range(len(lg))):
        ratings=[];ratings_gr=[]
        #1 ген-1статья
        print(lg[i]+": "+str(len(la[i])))
        l = la[i]
        for j in range(len(la[i])):
            #print(l)
            req = prepare_request(lg[i], l[j])
            resp = send_request(req, temperature=0)
            v = convert_to_number(resp)
            #print(v)
            ratings.append(v)
        #1 ген- группа статей
        #print(lg[i])
        l = la[i]
        for j in range(0,len(l),3):
            if len(l)-j<=2:
                break
            req = prepare_request_nart(lg[i],l[j:min(j+3,len(l))])
            resp = send_request(req, temperature=0)
            v = convert_to_number(resp)
            #print("All art")
            #print(v)
            ratings_gr.append(v)          
            gmetric = abs(v-np.mean(ratings[j:min(j+3,len(l))])) 
            gmetrics.append(gmetric)
            
    #print(gmetrics)
    metric = np.mean(gmetrics)
    #print(metric)
    return metric

# наличие в результате ссылок на гены упомянутые в других статьях
def calc_metric_crossgenes(articles, genes, filename="age_related_processes_change.json"):
    gm = check_genes(articles, genes)
    #узнали важность генов
    lgg, laa = make_list_genes_articles(genes, articles, gm)
    save_lists(lgg, laa, filename)
    
    gmetrics=[]    
    for k in range(len(lgg)):    
        lg = lgg[k]; la = laa[k]
        #print(lg[0])
        req = prepare_request_nart(lg[0],la)
        resp = send_request(req, temperature=0)
        v = convert_to_number(resp)
        #print(v)
        #print(lg[1])
        req = prepare_request_nart(lg[1],la)
        resp = send_request(req, temperature=0)
        v = convert_to_number(resp)
        #print(v)

        #проверили что в выдаче есть общие гены
        s=0
        #1 ген- все статьи
        #print(lg)
        req = prepare_request_cross(lg[0], la, long=False)
        resp = send_request(req,max_tokens=75)
        v = unidecode(resp)
        #print(v)
        if lg[1] in v:
            s=s+.5
        if lg[0] in v:
            s=s+.5
        gmetrics.append(s)
        
    metric = np.mean(gmetrics)
    #print(metric)
    return s



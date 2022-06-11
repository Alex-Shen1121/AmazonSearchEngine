import imp
from sys import meta_path
from xml.dom.minidom import parse
import xml.dom.minidom
import re
import jieba
import math
import json
import os
from matplotlib.pyplot import title

from requests import delete
from tensorboard import summary
import ParseJson
from tqdm import tqdm
import pickle
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


class InvertIndex:
    # 数据文件夹名
    file_path = ""
    # meta与review根据Asin合并后的Dict
    raw_data_metaPlusReview = {}
    # 原始的文档集合
    origin_doc_set = {}
    # 分词后的文档集合
    doc_set = {}
    # tokens列表
    tokens_lib = []
    # terms列表
    terms_lib = []
    # tokens数量
    tokens_num = 0
    # terms数量
    terms_num = 0
    # 倒排索引
    invert_index = {}
    # TF
    doc_TF = {}
    # IDF
    doc_IDF = []
    # TF-IDF
    doc_TFIDF = {}
    # json压缩包路径
    metaPath = './rawdata/meta_Gift_Cards.json.gz'
    wholeReviewPath = './rawdata/Gift_Cards.json.gz'
    partReviewPath = './rawdata/Gift_Cards_5.json.gz'

    def __init__(self, FilePath, type):
        self.file_path = FilePath
        if os.path.exists(self.file_path + "/built_index.json"):
            # 如果前面已经构建好了索引，则直接加载，不需要再重新计算
            print("正在加载已有索引")
            self.load_index()
        else:
            # 如果是第一次运行，则构建并保存索引，以便下次使用
            print("正在构建新索引")
            if not os.path.exists(self.file_path + f"/raw_data_metaPlusReview{type}.pkl"):
                self.create_rawData(type=type)
            self.createText(type=type)
            self.calculate_TFIDF()
            self.save_index()

    # 删除标点符号，并且将句子转化为list
    def deletePunctuation(self, str):
        str = re.split('[^a-zA-Z]', str)
        for l in str:
            while '' in str:
                str.remove('')
        # tokens转化为terms
        ps = PorterStemmer()
        res = set()
        for w in str:
            res.add(ps.stem(w))
        return res

    # tokens转化为terms
    def tokens_to_terms(self, tokens):
        ps = PorterStemmer()
        res = set()
        for w in tokens:
            res.add(ps.stem(w))
        return res

    # 创建原始数据集
    def create_rawData(self, type='test'):
        # 解析json文件
        metas = ParseJson.getDF(self.metaPath)
        if type == 'whole':
            reviews = ParseJson.getDF(self.wholeReviewPath)
        elif type == 'test':
            reviews = ParseJson.getDF(self.partReviewPath)

        # 根据asin ID将物品与评论进行关联
        for product in tqdm(metas.values()):
            # 类型检测，否则会有bug
            if not isinstance(product, dict):
                continue
            # 获取物品Asin
            productAsin = product['asin']
            self.raw_data_metaPlusReview[productAsin] = {
                'category': product['category'],
                'description': product['description'],
                'title': product['title'],
                'also_buy': product['also_buy'],
                'brand': product['brand'],
                'feature': product['feature'],
                'rank': product['rank'],
                'also_view': product['also_view'],
                'details': product['details'],
                'main_cat': product['main_cat'],
                'imageURLHighRes': product['imageURLHighRes']
            }
            self.raw_data_metaPlusReview[productAsin]['reviews'] = []

            # 遍历评论信息
            for review in reviews.values():
                if review['asin'] != productAsin:
                    continue
                # 类型检测，否则会有bug
                if not isinstance(review, dict):
                    continue
                if 'vote' not in review.keys():
                    review['vote'] = 0
                if 'image' not in review.keys():
                    review['image'] = []
                if 'reviewText' not in review.keys():
                    review['reviewText'] = ''
                if 'summary' not in review.keys():
                    review['summary'] = ''
                # 添加评论信息
                self.raw_data_metaPlusReview[productAsin]['reviews'].append({
                    'image': review['image'],
                    'overall': review['overall'],
                    'vote': review['vote'],
                    'reviewText': review['reviewText'],
                    'summary': review['summary'],
                })

        with open(f"./datasets/raw_data_metaPlusReview{type}.pkl", "wb") as fp:
            pickle.dump(self.raw_data_metaPlusReview, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        print("原始数据集创建完成")

    # 从原始数据中提取有效信息
    def createText(self, type='test', all=False, section=[]):
        print("正在加载原始数据集...")
        with open(f"./datasets/raw_data_metaPlusReview{type}.pkl", "rb") as fp:
            self.raw_data_metaPlusReview = pickle.load(fp)

        print("正在提取有效信息...")
        # 提取有效信息 变成list[]
        for asin in tqdm(self.raw_data_metaPlusReview.keys()):
            product = self.raw_data_metaPlusReview[asin]
            detail = ''
            for item in product['details'].items():
                detail += item[0] + ' ' + item[1] + ' '
            reviewText = ''
            for review in product['reviews']:
                reviewText += review['reviewText']
            reviewSummary = ''
            for review in product['reviews']:
                reviewSummary += review['summary']

            self.doc_set[asin] = {
                'category': self.deletePunctuation(' '.join(product['category'])),
                'description': self.deletePunctuation(' '.join(product['description'])),
                'title': self.deletePunctuation(product['title']),
                'brand': self.deletePunctuation(product['brand']),
                'feature': self.deletePunctuation(' '.join(product['feature'])),
                'details': self.deletePunctuation(detail),
                'main_cat': self.deletePunctuation(product['main_cat']),
                'reviewText': self.deletePunctuation(reviewText),
                'reviewSummary': self.deletePunctuation(reviewSummary)
            }

        # 构造tokens列表
        print("正在构造tokens列表...")
        for cut_doc in tqdm(self.doc_set.values()):
            for item in cut_doc.values():
                self.tokens_lib.extend(self.tokens_to_terms(item))
        # 计算tokens数量
        self.tokens_num = len(self.tokens_lib)
        # 剔除重复出现的tokens，构造terms列表
        self.terms_lib = list(set(self.tokens_lib))
        # 计算terms数量
        self.terms_num = len(self.terms_lib)

        # # 打印输出个数
        # print("token: " + str(self.tokens_num))
        # print("term: " + str(self.terms_num))

        # 构建倒排索引invert_index
        # 对于词库中的每一个term
        print("正在构建倒排索引...")
        for term in tqdm(self.terms_lib):
            temp_list = []
            # 看看文档集的每一个文档中有没有包含该token
            for j in self.doc_set:
                # 如果该文档包含了该token，那么就把这个文档的id加入这条倒排索引中
                for l in self.doc_set[j].values():
                    if term in l:
                        temp_list.append(j)
                        break
            self.invert_index[term] = temp_list

    def calculate_TFIDF(self):
        # 计算TF
        print("正在计算TF...")
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TF[asin] = [0.0] * self.terms_num
            for l in self.doc_set[asin].values():
                for token in l:
                    if token in self.terms_lib:
                        self.doc_TF[asin][self.terms_lib.index(token)] += 1.0
            i = 0
            for frequency in self.doc_TF[asin]:
                if self.doc_TF[asin][i] > 0:
                    self.doc_TF[asin][i] = (
                        1 + math.log(self.doc_TF[asin][i], 10))
                else:
                    self.doc_TF[asin][i] = 0
                i += 1

        # 计算IDF
        print("正在计算IDF...")
        # 每个词项在文档集中的出现次数
        self.doc_IDF = [0.0] * self.terms_num
        i = 0
        for term in tqdm(self.terms_lib):
            for doc in self.doc_set.values():
                for l in doc.values():
                    if term in l:
                        self.doc_IDF[i] += 1
            self.doc_IDF[i] = math.log(
                len(self.doc_set) / (self.doc_IDF[i]+1), 10)
            i += 1
        
        # 计算TF-IDF
        print("正在计算TF-IDF...")
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TFIDF[asin] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF[asin][i] = self.doc_TF[asin][i] * self.doc_IDF[i]

    def save_index(self):
        # 将要保存的内容组织好
        


if __name__ == '__main__':
    index_class = InvertIndex('./datasets', 'test')

    # index_class.create_rawData()

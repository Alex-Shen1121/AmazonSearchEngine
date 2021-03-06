import re
import math
import os
import ParseJson
from tqdm import tqdm
import pickle
from nltk.stem import PorterStemmer


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
    invert_index_title = {}
    invert_index_reviewtext = {}
    invert_index_feature = {}
    # TF
    doc_TF = {}
    # IDF
    doc_IDF = []
    # TF-IDF
    doc_TFIDF = {}
    doc_TFIDF_title = {}
    doc_TFIDF_reviewText = {}
    doc_TFIDF_feature = {}
    # json压缩包路径
    metaPath = './rawdata/meta_Gift_Cards.json.gz'
    wholeReviewPath = './rawdata/Gift_Cards.json.gz'
    partReviewPath = './rawdata/Gift_Cards_5.json.gz'

    def __init__(self, FilePath, type = 'test'):
        self.file_path = FilePath
        if os.path.exists(self.file_path + f"/{type}/invert_index_{type}.pkl"):
            # 如果前面已经构建好了索引，则直接加载，不需要再重新计算
            print("正在加载已有索引")
            self.load_index(type)
        else:
            # 如果是第一次运行，则构建并保存索引，以便下次使用
            print("正在构建新索引")
            self.create_rawData(type=type)
            self.createText(type=type)
            self.calculate_TFIDF(type=type)
            self.save_index(type=type)

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
                'price': product['price'],
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
                if 'reviewerName' not in review.keys():
                        review['reviewerName'] = ''
                # 添加评论信息
                self.raw_data_metaPlusReview[productAsin]['reviews'].append({
                    'image': review['image'],
                    'overall': review['overall'],
                    'vote': review['vote'],
                    'reviewText': review['reviewText'],
                    'summary': review['summary'],
                    'reviewTime': review['reviewTime'],
                    'reviewerName': review['reviewerName'],
                })

        print("原始数据集创建完成")

    # 从原始数据中提取有效信息
    def createText(self, type='test', all=False, section=[]):
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
        
        for term in tqdm(self.terms_lib):
            temp_list1 = []
            temp_list2 = []
            temp_list3 = []
            # 看看文档集的每一个文档中有没有包含该token
            for j in self.doc_set:
                if term in self.doc_set[j]['title']:
                    temp_list1.append(j)
                if term in self.doc_set[j]['reviewText']:
                    temp_list2.append(j)
                if term in self.doc_set[j]['feature']:
                    temp_list3.append(j)
            self.invert_index_title[term] = temp_list1
            self.invert_index_reviewtext[term] = temp_list2
            self.invert_index_feature[term] = temp_list3

    def calculate_TFIDF(self, type='test'):
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
                
        doc_TF_title = {}
        for asin in tqdm(self.doc_set.keys()):
            doc_TF_title[asin] = [0.0] * self.terms_num
            for l in self.doc_set[asin]['title']:
                for token in l:
                    if token in self.terms_lib:
                        doc_TF_title[asin][self.terms_lib.index(token)] += 1.0
            i = 0
            for frequency in doc_TF_title[asin]:
                if doc_TF_title[asin][i] > 0:
                    doc_TF_title[asin][i] = (
                        1 + math.log(doc_TF_title[asin][i], 10))
                else:
                    doc_TF_title[asin][i] = 0
                i += 1
        
        doc_TF_feature = {}
        for asin in tqdm(self.doc_set.keys()):
            doc_TF_feature[asin] = [0.0] * self.terms_num
            for l in self.doc_set[asin]['feature']:
                for token in l:
                    if token in self.terms_lib:
                        doc_TF_feature[asin][self.terms_lib.index(token)] += 1.0
            i = 0
            for frequency in doc_TF_feature[asin]:
                if doc_TF_feature[asin][i] > 0:
                    doc_TF_feature[asin][i] = (
                        1 + math.log(doc_TF_feature[asin][i], 10))
                else:
                    doc_TF_feature[asin][i] = 0
                i += 1
        
        doc_TF_reviewText = {}
        for asin in tqdm(self.doc_set.keys()):
            doc_TF_reviewText[asin] = [0.0] * self.terms_num
            for l in self.doc_set[asin]['reviewText']:
                for token in l:
                    if token in self.terms_lib:
                        doc_TF_reviewText[asin][self.terms_lib.index(token)] += 1.0
            i = 0
            for frequency in doc_TF_reviewText[asin]:
                if doc_TF_reviewText[asin][i] > 0:
                    doc_TF_reviewText[asin][i] = (
                        1 + math.log(doc_TF_reviewText[asin][i], 10))
                else:
                    doc_TF_reviewText[asin][i] = 0
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

        doc_IDF_title = [0.0] * self.terms_num
        i = 0
        for term in tqdm(self.terms_lib):
            for doc in self.doc_set.values():
                if term in doc['title']:
                    doc_IDF_title[i] += 1
            doc_IDF_title[i] = math.log(
                len(self.doc_set) / (doc_IDF_title[i]+1), 10)
            i += 1
        
        doc_IDF_feature = [0.0] * self.terms_num
        i = 0
        for term in tqdm(self.terms_lib):
            for doc in self.doc_set.values():
                if term in doc['feature']:
                    doc_IDF_feature[i] += 1
            doc_IDF_feature[i] = math.log(
                len(self.doc_set) / (doc_IDF_feature[i]+1), 10)
            i += 1

        doc_IDF_reviewText = [0.0] * self.terms_num
        i = 0
        for term in tqdm(self.terms_lib):
            for doc in self.doc_set.values():
                if term in doc['reviewText']:
                    doc_IDF_reviewText[i] += 1
            doc_IDF_reviewText[i] = math.log(
                len(self.doc_set) / (doc_IDF_reviewText[i]+1), 10)
            i += 1

        # 计算TF-IDF
        print("正在计算TF-IDF...")
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TFIDF[asin] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF[asin][i] = self.doc_TF[asin][i] * \
                    self.doc_IDF[i]
        
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TFIDF_title[asin] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF_title[asin][i] = doc_TF_title[asin][i] * \
                    doc_IDF_title[i]
        
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TFIDF_feature[asin] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF_feature[asin][i] = doc_TF_feature[asin][i] * \
                    doc_IDF_feature[i]
        
        for asin in tqdm(self.doc_set.keys()):
            self.doc_TFIDF_reviewText[asin] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF_reviewText[asin][i] = doc_TF_reviewText[asin][i] * \
                    doc_IDF_reviewText[i]

    def save_index(self, type='test'):
        print("正在保存各种索引...")
        # 保存各种索引
        with open(f"./datasets/{type}/raw_data_metaPlusReview_{type}.pkl", "wb") as fp:
            pickle.dump(self.raw_data_metaPlusReview, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_set_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_set, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/tokens_lib_{type}.pkl", "wb") as fp:
            pickle.dump(self.tokens_lib, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/terms_lib_{type}.pkl", "wb") as fp:
            pickle.dump(self.terms_lib, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/tokens_num_{type}.pkl", "wb") as fp:
            pickle.dump(self.tokens_num, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/terms_num_{type}.pkl", "wb") as fp:
            pickle.dump(self.terms_num, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/invert_index_{type}.pkl", "wb") as fp:
            pickle.dump(self.invert_index, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_TF_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_TF, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_IDF_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_IDF, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_TFIDF_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_TFIDF, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_TFIDF_title_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_TFIDF_title, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_TFIDF_feature_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_TFIDF_feature, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)
        with open(f"./datasets/{type}/doc_TFIDF_reviewText_{type}.pkl", "wb") as fp:
            pickle.dump(self.doc_TFIDF_reviewText, fp,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def load_index(self, type='test'):
        # 加载各种索引
        with open(f"./datasets/{type}/raw_data_metaPlusReview_{type}.pkl", "rb") as fp:
            self.raw_data_metaPlusReview = pickle.load(fp)
        with open(f"./datasets/{type}/doc_set_{type}.pkl", "rb") as fp:
            self.doc_set = pickle.load(fp)
        with open(f"./datasets/{type}/tokens_lib_{type}.pkl", "rb") as fp:
            self.tokens_lib = pickle.load(fp)
        with open(f"./datasets/{type}/terms_lib_{type}.pkl", "rb") as fp:
            self.terms_lib = pickle.load(fp)
        with open(f"./datasets/{type}/tokens_num_{type}.pkl", "rb") as fp:
            self.tokens_num = pickle.load(fp)
        with open(f"./datasets/{type}/terms_num_{type}.pkl", "rb") as fp:
            self.terms_num = pickle.load(fp)
        with open(f"./datasets/{type}/invert_index_{type}.pkl", "rb") as fp:
            self.invert_index = pickle.load(fp)
        with open(f"./datasets/{type}/doc_TF_{type}.pkl", "rb") as fp:
            self.doc_TF = pickle.load(fp)
        with open(f"./datasets/{type}/doc_IDF_{type}.pkl", "rb") as fp:
            self.doc_IDF = pickle.load(fp)
        with open(f"./datasets/{type}/doc_TFIDF_{type}.pkl", "rb") as fp:
            self.doc_TFIDF = pickle.load(fp)
        with open(f"./datasets/{type}/doc_TFIDF_title_{type}.pkl", "rb") as fp:
            self.doc_TFIDF_title = pickle.load(fp)
        with open(f"./datasets/{type}/doc_TFIDF_feature_{type}.pkl", "rb") as fp:
            self.doc_TFIDF_feature = pickle.load(fp)
        with open(f"./datasets/{type}/doc_TFIDF_reviewText_{type}.pkl", "rb") as fp:
            self.doc_TFIDF_reviewText = pickle.load(fp)

if __name__ == '__main__':
    index_class = InvertIndex('./datasets', 'test')

    # index_class.create_rawData()

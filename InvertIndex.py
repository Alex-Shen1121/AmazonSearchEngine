from xml.dom.minidom import parse
import xml.dom.minidom
import re
import jieba
import math
import json
import os


class InvertIndex:
    # 数据文件夹名
    file_path = ""
    # 文档的总数量
    doc_num = 1000  # 可选的范围为[1,2449]
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

    def __init__(self, FilePath):
        self.file_path = FilePath
        if os.path.exists(self.file_path + "/built_index.json"):
            # 如果前面已经构建好了索引，则直接加载，不需要再重新计算
            print("正在加载已有索引")
            self.load_index()
        else:
            # 如果是第一次运行，则构建并保存索引，以便下次使用
            print("正在构建新索引")
            self.creat()
            self.calculate_TFIDF()
            self.save_index()

    def creat(self):
        doc_id = 0
        # 逐文件读取
        for file_name in range(self.doc_num):
            DOMTree = xml.dom.minidom.parse(self.file_path + "/news/" + str(doc_id) + ".xml")
            collection = DOMTree.documentElement
            title = collection.getElementsByTagName('title')[0].childNodes[0].nodeValue
            content = collection.getElementsByTagName('body')[0].childNodes[0].nodeValue
            date_time = collection.getElementsByTagName('datetime')[0].childNodes[0].nodeValue
            self.origin_doc_set[doc_id] = {"title": title, "content": content, "datetime": date_time}
            doc_id += 1

        # 载入词典，使分词更精准
        jieba.set_dictionary("./datasets/dict.txt")
        # 加载所有的文档并对每个文档进行分词，然后用一个字典doc_set保存
        id = 0
        for doc in self.origin_doc_set.values():
            # 将大写字母转成小写
            title = doc['title'].lower()
            content = doc['content'].lower()
            # 用正则表达式去除标点，只保留"中文"、"大小写英文字母"、"数字"
            title = re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", " ", title)
            content = re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", " ", content)
            # jieba分词，全切割模式
            cut_title = list(jieba.cut(title, cut_all=True))
            cut_title = list(filter(lambda x: x != '', cut_title))
            cut_title = list(filter(lambda x: x != ' ', cut_title))
            cut_content = list(jieba.cut(content, cut_all=True))
            cut_content = list(filter(lambda x: x != '', cut_content))
            cut_content = list(filter(lambda x: x != ' ', cut_content))
            cut_title_content = []
            cut_content.extend(cut_title)
            cut_title_content.extend(cut_content)
            self.doc_set[id] = {"title": cut_title, "content": cut_content, "title_content": cut_title_content}
            id += 1
            # 先读doc_num条测试一下
            if id >= self.doc_num:
                break

        # 打印输出文档集 ############################################################################
        # for i in self.origin_doc_set:
        #     print(i)
        # for i in self.doc_set:
        #     print(str(i) + "：" + str(self.doc_set[i]))

        # 构造tokens列表
        for cut_doc in self.doc_set.values():
            self.tokens_lib.extend(cut_doc["title_content"])
        # 计算tokens数量
        self.tokens_num = len(self.tokens_lib)
        # 剔除重复出现的tokens，构造terms列表
        self.terms_lib = list(set(self.tokens_lib))
        # 计算terms数量
        self.terms_num = len(self.terms_lib)

        # 打印输出个数 ##############################################################################
        # print("token: " + str(self.tokens_num))
        # print("term: " + str(self.terms_num))

        # 构建倒排索引invert_index
        # 对于词库中的每一个term
        for i in self.terms_lib:
            temp_list = []
            # 看看文档集的每一个文档中有没有包含该token
            for j in self.doc_set:
                # 如果该文档包含了该token，那么就把这个文档的id加入这条倒排索引中
                if i in self.doc_set[j]["title_content"]:
                    temp_list.append(j)
            self.invert_index[i] = temp_list

        # 打印输出倒排索引invert_index ##############################################################
        # for i in self.invert_index:
        #     print(str(i) + "：" + str(self.invert_index[i]))

    def calculate_TFIDF(self):
        # 计算TF
        # overall_TF = [0] * self.terms_num   # 文档集中所有的term出现的频数
        for id in self.doc_set.keys():
            self.doc_TF[id] = [0.0] * self.terms_num
            for token in self.doc_set[id]['title_content']:
                if token in self.terms_lib:
                    self.doc_TF[id][self.terms_lib.index(token)] += 1.0
                    # overall_TF[self.terms_lib.index(token)] += 1 # 文档集中所有的term出现的频数
            i = 0
            for frequency in self.doc_TF[id]:
                if self.doc_TF[id][i] > 0:
                    self.doc_TF[id][i] = (1 + math.log(self.doc_TF[id][i], 10))
                else:
                    self.doc_TF[id][i] = 0
                i += 1
        # 打印输出TF ##############################################################
        # for k in self.doc_TF:
        #     print(str(k) + "：" + str(self.doc_TF[k]))

        # 排序并输出整个文档集中所有的term，以及它们出现的频数
        # temp = []
        # temp.extend(self.terms_lib)
        # for i in range(self.terms_num):
        #     max_index = i
        #     for j in range(i + 1, self.terms_num):
        #         if overall_TF[j] > overall_TF[max_index]:
        #             max_index = j
        #     if max_index != i:
        #         a = temp[i]
        #         temp[i] = temp[max_index]
        #         temp[max_index] = a
        #         b = overall_TF[i]
        #         overall_TF[i] = overall_TF[max_index]
        #         overall_TF[max_index] = b
        # print(temp)
        # print(overall_TF)

        # 计算IDF
        self.doc_IDF = [0.0] * self.terms_num
        i = 0
        for term in self.terms_lib:
            for doc in self.doc_set.values():
                if term in doc['title_content']:
                    self.doc_IDF[i] += 1
            self.doc_IDF[i] = math.log(self.doc_num / self.doc_IDF[i], 10)
            i += 1
        # 打印输出IDF ##############################################################
        # print(self.doc_IDF)

        # 计算TF-IDF
        for id in self.doc_set.keys():
            self.doc_TFIDF[id] = [0.0] * self.terms_num
            for i in range(self.terms_num):
                self.doc_TFIDF[id][i] = self.doc_TF[id][i] * self.doc_IDF[i]
        # 打印输出TF-IDF ###########################################################
        # for k in self.doc_TFIDF.keys():
        #     print(str(k) + "：" + str(self.doc_TFIDF[k]))

    def save_index(self):
        # 将要保存的内容组织好
        dict_to_save = {
            'file_path': self.file_path,
            'doc_num': self.doc_num,
            'origin_doc_set': self.origin_doc_set,
            'doc_set': self.doc_set,
            'tokens_lib': self.tokens_lib,
            'terms_lib': self.terms_lib,
            'tokens_num': self.tokens_num,
            'terms_num': self.terms_num,
            'invert_index': self.invert_index,
            'doc_TF': self.doc_TF,
            'doc_IDF': self.doc_IDF,
            'doc_TFIDF': self.doc_TFIDF
        }
        # 保存为一个json文件
        js = json.dumps(dict_to_save, ensure_ascii=False)  # ensure_ascii=False用于解决中文乱码
        file = open('./datasets/built_index.json', 'w', encoding="utf-8")
        file.write(js)
        file.close()

    def load_index(self):
        # 打开json文件
        file = open("./datasets/built_index.json", "r", encoding="utf-8")
        # 读取json文件的内容，生成一个字典
        dic = json.load(file)
        # 关闭json文件
        file.close()
        # 逐项加载数据
        self.doc_num = dic['doc_num']
        self.tokens_lib = dic['tokens_lib']
        self.terms_lib = dic['terms_lib']
        self.tokens_num = dic['tokens_num']
        self.terms_num = dic['terms_num']
        self.invert_index = dic['invert_index']
        self.doc_IDF = dic['doc_IDF']

        self.origin_doc_set = dic['origin_doc_set']  #
        self.doc_set = dic['doc_set']  #
        self.doc_TF = dic['doc_TF']  #
        self.doc_TFIDF = dic['doc_TFIDF']  #

        # 因为读入时会将int类型的键变为string类型，所以我们要先处理一下
        for i in range(self.doc_num):
            self.origin_doc_set[i] = self.origin_doc_set[str(i)]
            del self.origin_doc_set[str(i)]
            self.doc_set[i] = self.doc_set[str(i)]
            del self.doc_set[str(i)]
            self.doc_TF[i] = self.doc_TF[str(i)]
            del self.doc_TF[str(i)]
            self.doc_TFIDF[i] = self.doc_TFIDF[str(i)]
            del self.doc_TFIDF[str(i)]

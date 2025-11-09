import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class QAIndex:
    def __init__(self, qa_pairs: list[tuple[str, str]]):
        if qa_pairs:
            self.questions, self.answers = zip(*qa_pairs)
        else:
            self.questions, self.answers = [], []
        self.vectorizer = TfidfVectorizer()
        if self.questions:
            self.matrix = self.vectorizer.fit_transform(self.questions)
        else:
            self.matrix = None

    @classmethod
    def from_csv(cls, path: str):
        df = pd.read_csv(path)
        qa = [(str(q), str(a)) for q, a in zip(df["question"], df["answer"])]
        return cls(qa)

    def ask(self, query: str, topk: int = 1):
        if not self.questions:
            return []
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix).ravel()
        idx = sims.argsort()[::-1][:topk]
        return [(self.questions[i], self.answers[i], float(sims[i])) for i in idx]

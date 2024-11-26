class Labels:
    def __init__(self, path: str, other_label: str = "その他"):
        self.labels = [other_label]
        self.other_label = other_label

        with open(path) as f:
            for line in f:
                self.append_unique(line.strip())

    def id(self, label: str):
        return self.labels.index(label) + 1

    def label(self, id: int):
        return self.labels[id - 1]

    def __call__(self, x):
        return self.labels[x]

    def __len__(self):
        return len(self.labels)

    def __iter__(self):
        return iter(self.labels)

    def __getitem__(self, x):
        return self.labels[x]

    def __setitem__(self, x, value):
        self.labels[x] = value

    def append_unique(self, value):
        if value not in self.labels:
            self.labels.append(value)

    def other(self):
        return self.other_label

    def other_id(self):
        return self.id(self.other_label)

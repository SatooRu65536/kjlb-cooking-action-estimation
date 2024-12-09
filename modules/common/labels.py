import matplotlib.colors as mcolors


class Labels:
    colors = list(mcolors.CSS4_COLORS)

    def __init__(
        self,
        path: str,
        other_label: str = "その他",
        unuse_label: str = "不要",
        group_labels: dict[str, list[str]] = {},
    ):
        self.labels = [other_label]
        self.other_label = other_label
        self.unuse_label = unuse_label
        self._unuse_id = -1
        self.group_labels = group_labels

        with open(path) as f:
            for line in f:
                self.append_unique(line.strip())

    def id(self, label: str):
        if label not in self.labels:
            return self.other_id()

        return self.labels.index(label)

    def label(self, id: int):
        if id == self.unuse_id():
            return self.other_label
        return self.labels[id]

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
        for group, labels in self.group_labels.items():
            if value in labels:
                value = group
                break

        if value not in self.labels and value != self.unuse_label:
            self.labels.append(value)

    def other(self):
        return self.other_label

    def other_id(self):
        return self.id(self.other_label)

    def unuse(self):
        return self.unuse_label

    def unuse_id(self):
        return self._unuse_id

    def color_by_id(self, id: int):
        return self.colors[id]

    def color_by_label(self, label: str):
        return self.colors[self.id(label)]

    def color_list(self):
        return self.colors

    def color_dict(self):
        return {label: self.colors[i] for i, label in enumerate(self.labels)}

import os
import glob

OUTPUT_BASE_DIR = "./data/output/all/each_process2"


def get_result_files(output_dir: str):
    return glob.glob(os.path.join(output_dir, "**/result_4_5.txt"))


def get_data(file_path: str):
    metadata: dict[str, str | float] = {}

    basename = os.path.basename(os.path.dirname(file_path))
    metadata["model"] = basename.split("_")[0]
    metadata["segment_window_size"] = int(basename.split("segmentw")[1].split("_")[0])
    metadata["segment_gap_size"] = int(basename.split("segmentgap")[1].split("_")[0])
    metadata["smooth_window_size"] = int(basename.split("smoothw")[1].split("_")[0])

    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            key_, value_ = line.split(":")
            key = key_.strip()
            value = value_.strip()
            metadata[key] = float(value)

    return metadata


def group_by(data_list: list[dict[str, str | float]], key="model"):
    grouped_data: dict[str | float, list[dict[str, str | float]]] = {}
    for data in data_list:
        model = data[key]
        if model not in grouped_data:
            grouped_data[model] = []
        grouped_data[model].append(data)

    return grouped_data


def to_table(
    data: dict[str, str | float],
    row="segment_window_size",
    column="smooth_window_size",
    value="smoothed_accurary",
):
    column_values: list[str | float] = sorted(set([d[column] for d in data]))
    column_values.insert(0, "")
    table: list[list[str | float]] = [column_values]
    for row_value in sorted(set([d[row] for d in data])):
        row_data: list[str | float] = [row_value]
        for column_value in sorted(set([d[column] for d in data])):
            filtered_data = [
                d for d in data if d[row] == row_value and d[column] == column_value
            ]
            if len(filtered_data) == 0:
                row_data.append("N/A")
            else:
                row_data.append(filtered_data[0][value])
        table.append(row_data)

    return table


def main():
    result_files = get_result_files(OUTPUT_BASE_DIR)
    data_list = [get_data(file_path) for file_path in result_files]

    grouped_data = group_by(data_list, key="model")
    for model, data in grouped_data.items():
        print(f"\n== {model} ==")
        table = to_table(data, value="smoothed_accurary")
        # table = to_table(data, value="top_k_accurary")

        cols = ", ".join([f'"{row / 60}s"' for row in table[0][1:]])
        rows = ", ".join([f'"{row[0] / 60}s"' for row in table[1:]])
        cells = ",\n".join(
            [
                f"({c})"
                for c in [
                    ", ".join(
                        [
                            f"[{cell:.3f}]" if type(cell) != str else f'"{cell}"'
                            for cell in row[1:]
                        ]
                    )
                    for row in table[1:]
                ]
            ]
        )
        print(
            f"""
cols: ({cols}),
rows: ({rows}),
cells: ({cells}),"""
        )

        print()
        for row in table:
            for cell in row:
                print(cell, end=",")
            print()


if __name__ == "__main__":
    main()

export interface Label {
  meta: {
    // 動画開始時間とセンシング開始時間の差
    offset: number;
    // 料理した人の名前
    name: string;
    // その人の何回目の料理か
    count: number;
    // 動画のURL
    video_url?: string;
    // フレーム数
    frames: number;
    // フレームレート
    frame_rate: number;
    // 時間の指定方法
    type: "frame" | "time";
  };
  labels: string[];
  label_range: {
    start: number;
    end: number;
    label: number;
  }[];
}

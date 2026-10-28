import argparse
import csv
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


def _clip_start(path: str, modified: str, line_number: int) -> datetime:
    filename = Path(path.replace("\\", "/")).name
    try:
        return datetime.strptime(Path(filename).stem, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        try:
            return datetime.strptime(modified, "%Y:%m:%d  %H:%M:%S:%f")
        except ValueError as error:
            raise ValueError(
                f"Could not parse a footage timestamp on CSV line {line_number}"
            ) from error


def _camera_name(full_path: str, line_number: int) -> str:
    parts = [part for part in full_path.replace("\\", "/").split("/") if part]
    date_folder = next(
        (index for index, part in enumerate(parts) if re.fullmatch(r"\d{8}", part)),
        None,
    )
    camera_index = date_folder - 1 if date_folder is not None else len(parts) - 2
    if camera_index < 0:
        raise ValueError(f"Could not determine camera folder on CSV line {line_number}")

    name = parts[camera_index]
    if name.lower().endswith("_partials"):
        name = name[: -len("_partials")]
    return name


def read_footage(csv_path: Path) -> dict[str, list[datetime]]:
    footage: dict[str, list[datetime]] = defaultdict(list)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        for line_number, row in enumerate(csv.reader(file, delimiter=";"), start=1):
            if not row or not row[0].lower().endswith(".mkv"):
                continue
            if len(row) < 4:
                raise ValueError(f"Expected four columns on CSV line {line_number}")

            camera = _camera_name(row[3], line_number)
            footage[camera].append(_clip_start(row[0], row[2], line_number))

    if not footage:
        raise ValueError(f"No .mkv footage entries found in {csv_path}")

    return {
        camera: sorted(set(starts))
        for camera, starts in sorted(footage.items())
    }


def _availability_blocks(
    starts: list[datetime],
) -> tuple[list[tuple[datetime, datetime]], timedelta]:
    gaps = [
        later - earlier
        for earlier, later in zip(starts, starts[1:])
        if later > earlier
    ]
    clip_duration = median(gaps) if gaps else timedelta(seconds=6)

    blocks: list[tuple[datetime, datetime]] = []
    for start in starts:
        end = start + clip_duration
        if blocks and start <= blocks[-1][1]:
            blocks[-1] = (blocks[-1][0], max(blocks[-1][1], end))
        else:
            blocks.append((start, end))

    return blocks, clip_duration


def plot_footage(footage: dict[str, list[datetime]], output: Path | None) -> None:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    figure_height = max(3.0, len(footage) * 0.8 + 1.5)
    figure, axis = plt.subplots(figsize=(12, figure_height))

    for row, (camera, starts) in enumerate(footage.items()):
        blocks, _ = _availability_blocks(starts)
        for start, end in blocks:
            axis.barh(
                row,
                mdates.date2num(end) - mdates.date2num(start),
                left=mdates.date2num(start),
                height=0.55,
                color="tab:blue",
            )

    axis.set_yticks(range(len(footage)), labels=list(footage))
    axis.invert_yaxis()
    axis.set_xlabel("Date and time")
    axis.set_ylabel("Camera channel")
    axis.set_title("Available Footage by Camera")
    axis.xaxis.set_major_locator(mdates.AutoDateLocator())
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(axis.xaxis.get_major_locator()))
    axis.grid(axis="x", linestyle=":", alpha=0.7)
    figure.tight_layout()

    if output is None:
        plt.show()
    else:
        figure.savefig(output, dpi=150)
        print(f"Timeline saved to {output}")

    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot available DVR footage by camera channel."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).with_name("FileList.csv"),
        help="Semicolon-delimited file list (default: FileList.csv beside this script)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save the timeline to an image instead of opening a window",
    )
    args = parser.parse_args()

    footage = read_footage(args.csv)
    clip_count = sum(len(starts) for starts in footage.values())
    print(f"Found {clip_count} clips across {len(footage)} camera channels.")
    plot_footage(footage, args.output)


if __name__ == "__main__":
    main()
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

'''
03/11/2016 17:16:56 Storage: Starting thread

03/11/2016 17:16:56 DVR: StatMon - setting time to 2026-10-12 15:21:58

07/10/2026 11:28:25 Storage: Found active volume /media/sda1

07/10/2026 11:28:26 Volume /media/sda1: 3936819515392 free, 92422144 used, 3936911937536 total (99% free)

12/10/2026 15:22:03 DVR: StatMon - DVR Firmware Version: 2.18-3

'''

class MountTime:
    def __init__(
        self,
        occurrence: int,
        start_time: datetime,
        end_time: datetime,
        storage_free_percent: int,
        firmware_version: str,
    ):
        self.occurrence = occurrence
        self.start_time = start_time
        self.end_time = end_time
        self.storage_free_percent = storage_free_percent
        self.firmware_version = firmware_version
        self.time_taken = self.time_taken()

    def time_taken(self):
        if self.start_time is None or self.end_time is None:
            return timedelta(0)
        if self.end_time < self.start_time:
            return timedelta(0)
        return self.end_time - self.start_time

class MountTimeParser:
    def __init__(self, log_file_path: Path | str):
        self.log_file_path = log_file_path
        self.mount_times = self.parse_mount_time()

    def parse_mount_time(self) -> list[MountTime]:
        mount_times = []
        occurrence = 0
        started = False
        start_time = None
        end_time = None
        storage_free_percent = None
        firmware_version = None

        log_text = self.log_file_path.read_text(encoding="utf-8", errors="replace")

        for line_number, line in enumerate(log_text.splitlines(), start=1):

            if "Storage: Starting thread" in line:
                occurrence += 1
                started = True
                #
                start_time = None
                end_time = None
                storage_free_percent = None
                firmware_version = None
                #print(f"Occurrence {occurrence} started at line {line_number}")
                continue

            if not started:
                continue

            if "DVR: StatMon - setting time to" in line:
                start_time = self._parse_clock_set_time(line, line_number)
                #print(f"Occurrence {occurrence} clock set time found at line {line_number}: {start_time}")
                continue

            if "Storage: Found active volume /media/sda1" in line:
                end_time = self._parse_active_volume_time(line, line_number)
                #print(f"Occurrence {occurrence} active volume found at line {line_number}")
                continue

            if "Volume /media/sda1:" in line:
                storage_free_percent = self._parse_storage_free_percent(line, line_number)
                #print(f"Occurrence {occurrence} storage free percent found at line {line_number}: {storage_free_percent}%")
                continue

            if "DVR: StatMon - DVR Firmware Version:" in line:
                firmware_version = self._parse_firmware_version(line, line_number)
                #print(f"Occurrence {occurrence} firmware version found at line {line_number}: {firmware_version}")
                continue


            if (
                start_time is not None and
                end_time is not None and
                storage_free_percent is not None and
                firmware_version is not None
            ):
                mount_times.append(
                    MountTime(
                        occurrence=occurrence,
                        start_time=start_time,
                        end_time=end_time,
                        storage_free_percent=storage_free_percent,
                        firmware_version=firmware_version
                    )
                )

                started = False

        return mount_times

    def _parse_clock_set_time(self,line: str, line_number: int) -> Optional[datetime]:
        if "DVR: StatMon - setting time to" not in line:
            return None

        match = re.search(
            r"DVR: StatMon - setting time to "
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            line,
        )
        if match is None:
            raise ValueError(f"Could not parse clock-set time on line {line_number}")
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")


    def _parse_active_volume_time(self,line: str, line_number: int) -> Optional[datetime]:
        if "Storage: Found active volume /media/sda1" not in line:
            return None

        match = re.match(r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})", line)
        if match is None:
            raise ValueError(f"Could not parse active-volume time on line {line_number}")
        return datetime.strptime(match.group(1), "%d/%m/%Y %H:%M:%S")


    def _parse_storage_free_percent(self,line: str, line_number: int) -> Optional[int]:
        if "Volume /media/sda1:" not in line:
            return None

        match = re.search(r"\((\d+)% free\)", line)
        if match is None:
            raise ValueError(f"Could not parse free percentage on line {line_number}")
        return int(match.group(1))

    def _parse_firmware_version(self,line: str, line_number: int) -> Optional[str]:
        if "DVR: StatMon - DVR Firmware Version:" not in line:
            return None

        match = re.search(r"DVR: StatMon - DVR Firmware Version: (.+)", line)
        if match is None:
            raise ValueError(f"Could not parse firmware version on line {line_number}")
        return match.group(1)

class PlotMountTime:
    def __init__(self, mount_times: list[MountTime]):
        self.mount_times = mount_times

    def plot(self):
        import matplotlib.pyplot as plt

        occurrences = [mt.occurrence for mt in self.mount_times]
        start_times = [mt.start_time for mt in self.mount_times]
        time_taken = [mt.time_taken.total_seconds() for mt in self.mount_times]
        storage_free_percent = [mt.storage_free_percent for mt in self.mount_times]

        fig, ax1 = plt.subplots()

        color = 'tab:blue'
        ax1.set_xlabel('Occurrence (start date and time)')
        ax1.set_ylabel('Time Taken (seconds)', color=color)
        ax1.plot(occurrences, time_taken, color=color, marker='s', markersize=4)
        ax1.set_xticks(occurrences)
        ax1.set_xticklabels(
            [
                f'{start_time:%m-%d %H:%M}'
                for occurrence, start_time in zip(occurrences, start_times)
            ],
            rotation=90,
        )
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(axis='y', linestyle=':', alpha=0.85, color='gray')

        previous_firmware = None
        for mount_time in self.mount_times:
            if mount_time.firmware_version != previous_firmware:
                ax1.axvline(
                    mount_time.occurrence,
                    color='red',
                    linestyle=':',
                )
                ax1.annotate(
                    mount_time.firmware_version,
                    xy=(mount_time.occurrence, 0.98),
                    xycoords=ax1.get_xaxis_transform(),
                    textcoords='offset points',
                    xytext=(5, 0),
                    color='red',
                    rotation=90,
                    va='top',
                    ha='left',
                )
                previous_firmware = mount_time.firmware_version

        ax2 = ax1.twinx()
        ax1.set_zorder(ax2.get_zorder() + 1)
        ax1.patch.set_visible(False)
        color = 'tab:red'
        ax2.set_ylabel('Storage Free Percent', color=color)
        ax2.plot(occurrences, storage_free_percent, color=color, marker='s', markersize=4)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()
        plt.title('Mount Time and Storage Free Percent Over Time')
        plt.show()

if __name__ == "__main__":
    log_file_path = Path(__file__).with_name("dvr.log")
    parser = MountTimeParser(log_file_path)
    mount_times = parser.parse_mount_time()
    print(len(mount_times), "mount times found:")

    plotter = PlotMountTime(mount_times)
    plotter.plot()

    # for mount_time in mount_times:
    #     print(
    #         f"Occurrence {mount_time.occurrence}: "
    #         f"Start: {mount_time.start_time}, "
    #         f"End: {mount_time.end_time}, "
    #         f"Time taken: {mount_time.time_taken}, "
    #         f"Storage free: {mount_time.storage_free_percent}%, "
    #         f"Firmware version: {mount_time.firmware_version}"
    #     )
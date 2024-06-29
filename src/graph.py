import datetime

import matplotlib.dates as mdates


class Graph:
    def __init__(self, db_manager, happy_figure, emotion_figure, emotion_app):
        self.db_manager = db_manager
        self.happy_figure = happy_figure
        self.emotion_figure = emotion_figure
        self.emotion_app = emotion_app

    def on_tab_changed(self, index):
        if index == 0:
            if not self.happy_tab_viewed:
                self.show_happy_trend_day(True)
                self.happy_tab_viewed = True
                self.current_happy_button = self.emotion_app.happy_day_button
            else:
                selected_button = self.get_selected_button(
                    self.emotion_app.happy_button_layout
                )
                self.current_happy_button = (
                    selected_button
                    if selected_button
                    else self.emotion_app.happy_day_button
                )
                self.update_tab_styles(
                    self.current_happy_button, self.emotion_app.happy_button_layout
                )
        elif index == 1:
            if not self.emotion_tab_viewed:
                self.show_emotion_trend_day(True)
                self.emotion_tab_viewed = True
                self.current_emotion_button = self.emotion_app.emotion_day_button
            else:
                selected_button = self.get_selected_button(
                    self.emotion_app.emotion_button_layout
                )
                self.current_emotion_button = (
                    selected_button
                    if selected_button
                    else self.emotion_app.emotion_day_button
                )
                self.update_tab_styles(
                    self.current_emotion_button, self.emotion_app.emotion_button_layout
                )

    def get_selected_button(self, button_layout):
        for i in range(button_layout.count()):
            button = button_layout.itemAt(i).widget()
            if button.styleSheet() == "background-color: blue; color: white;":
                return button
        return None

    def update_tab_styles(self, selected_button, button_layout):
        for i in range(button_layout.count()):
            button = button_layout.itemAt(i).widget()
            if button == selected_button:
                button.setStyleSheet("background-color: blue; color: white;")
            else:
                button.setStyleSheet("")

    def show_emotion_trend_day(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_time = datetime.datetime.combine(today, datetime.time(6, 0))
        end_time = datetime.datetime.combine(today, datetime.time(18, 0))

        emotion_counts = self.db_manager.get_emotion_counts(start_time, end_time)
        hours_in_day = 13
        emotions = set([count[1] for count in emotion_counts])
        emotion_data = {emotion: [0] * hours_in_day for emotion in emotions}

        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if 6 <= timestamp.hour <= 18:
                hour_index = timestamp.hour - 6
                emotion_data[emotion][hour_index] += count

        times = [start_time + datetime.timedelta(hours=i) for i in range(hours_in_day)]

        self.plot_day_trend(
            self.emotion_figure,
            "Emotions Over the Day",
            "Hour of the Day",
            "Count of Emotions",
            emotion_data,
            times,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.emotion_day_button,
                self.emotion_app.emotion_button_layout,
            )
            self.current_emotion_button = self.emotion_app.emotion_day_button

    def show_emotion_trend_month(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(
            day=1
        ) - datetime.timedelta(days=1)

        emotion_counts = self.db_manager.get_emotion_counts(
            start_of_month, end_of_month
        )
        days_in_month = (end_of_month - start_of_month).days + 1
        emotions = set([count[1] for count in emotion_counts])
        emotion_data = {emotion: [0] * days_in_month for emotion in emotions}

        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            day_index = (timestamp.date() - start_of_month).days
            emotion_data[emotion][day_index] += count

        dates = [
            start_of_month + datetime.timedelta(days=i) for i in range(days_in_month)
        ]

        month_name = start_of_month.strftime("%B")
        self.plot_month_trend(
            self.emotion_figure,
            f"Emotions Over the Month {month_name}",
            "Date",
            "Count of Emotions",
            emotion_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.emotion_month_button,
                self.emotion_app.emotion_button_layout,
            )
            self.current_emotion_button = self.emotion_app.emotion_month_button

    def show_emotion_trend_year(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        emotion_counts = self.db_manager.get_emotion_counts(start_of_year, end_of_year)
        months_in_year = 12
        emotions = set([count[1] for count in emotion_counts])
        emotion_data = {emotion: [0] * months_in_year for emotion in emotions}

        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            month_index = timestamp.month - 1
            emotion_data[emotion][month_index] += count

        dates = [start_of_year.replace(month=i + 1) for i in range(months_in_year)]

        self.plot_year_trend(
            self.emotion_figure,
            "Emotions Over the Year",
            "Month",
            "Count of Emotions",
            emotion_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.emotion_year_button,
                self.emotion_app.emotion_button_layout,
            )
            self.current_emotion_button = self.emotion_app.emotion_year_button

    def show_happy_trend_day(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_today = datetime.datetime.combine(today, datetime.time(6, 0))
        end_of_today = datetime.datetime.combine(today, datetime.time(18, 0))

        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_today, end_of_today
        )
        counts = [0] * 13

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if 6 <= timestamp.hour <= 18:
                counts[timestamp.hour - 6] += count

        happy_data = {"Happy": counts}
        times = [start_of_today + datetime.timedelta(hours=i) for i in range(13)]

        self.plot_day_trend(
            self.happy_figure,
            "Happy Emotions Over the Work Hours of Today",
            "Hour of the Day",
            "Count of Happy Emotions",
            happy_data,
            times,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.happy_day_button, self.emotion_app.happy_button_layout
            )
            self.current_happy_button = self.emotion_app.happy_day_button

    def show_happy_trend_week(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_time = datetime.datetime.combine(start_of_week, datetime.time(6, 0))
        end_time = datetime.datetime.combine(
            start_of_week + datetime.timedelta(days=4), datetime.time(18, 0)
        )

        happy_counts = self.db_manager.get_happy_emotion_counts_for_week(
            start_time, end_time
        )
        days_in_week = 5
        happy_data = {"Happy": [0] * days_in_week}

        for date_str, hour_str, count in happy_counts:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if start_of_week <= date <= end_time.date():
                day_index = (date - start_of_week).days
                happy_data["Happy"][day_index] += count

        dates = [
            start_of_week + datetime.timedelta(days=i) for i in range(days_in_week)
        ]

        self.plot_week_trend(
            self.happy_figure,
            "Happy Emotions Over the Workweek",
            "Day of the Week",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.happy_week_button, self.emotion_app.happy_button_layout
            )
            self.current_happy_button = self.emotion_app.happy_week_button

    def show_happy_trend_month(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(
            day=1
        ) - datetime.timedelta(days=1)

        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_month, end_of_month
        )
        days_in_month = (end_of_month - start_of_month).days + 1
        happy_data = {"Happy": [0] * days_in_month}

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            day_index = (timestamp.date() - start_of_month).days
            happy_data["Happy"][day_index] += count

        dates = [
            start_of_month + datetime.timedelta(days=i) for i in range(days_in_month)
        ]

        month_name = start_of_month.strftime("%B")
        self.plot_month_trend(
            self.happy_figure,
            f"Happy Emotions Over the Month {month_name}",
            "Date",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.happy_month_button,
                self.emotion_app.happy_button_layout,
            )
            self.current_happy_button = self.emotion_app.happy_month_button

    def show_happy_trend_year(self, update_styles=False):
        today = datetime.datetime.now().date()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_year, end_of_year
        )
        months_in_year = 12
        happy_data = {"Happy": [0] * months_in_year}

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            month_index = timestamp.month - 1
            happy_data["Happy"][month_index] += count

        dates = [start_of_year.replace(month=i + 1) for i in range(months_in_year)]

        self.plot_year_trend(
            self.happy_figure,
            "Happy Emotions Over the Year",
            "Month",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_app.happy_year_button, self.emotion_app.happy_button_layout
            )
            self.current_happy_button = self.emotion_app.happy_year_button

    def plot_day_trend(self, figure, title, xlabel, ylabel, data, times):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(times, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_week_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a"))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_month_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_year_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

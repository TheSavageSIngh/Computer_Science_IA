from All_Imports.all_imports import *

kv = Builder.load_file("Charts_and_Graphs/charts_and_graphs.kv")


class GraphSwiperItem(MDSwiperItem):
    def __init__(self, graph, **kwargs):
        super().__init__(**kwargs)
        self.ids.custom_graph_card.add_widget(graph)


class ChartsAndGraphs(MDScreen):
    toolbar_date = toolbar_date

    def __init__(self, **kw):
        super().__init__(**kw)
        self.formatted_date_range = []
        self.create_subject_picker_menu()

    # date range
    def open_date_picker(self):
        date_picker = \
            MDDatePicker(mode="range", date_range_text_error="Please enter a valid date range!",
                         min_year=int(data_date[6:]) - 5, max_year=int(data_date[6:]), day=2,
                         text_button_color=hex_color("#0C6170"), accent_color=hex_color("#DBF5F0"),
                         text_weekday_color=hex_color("#000000"), selector_color=hex_color("#00A08D"),
                         input_field_text_color=hex_color("#212121"), primary_color=hex_color("#37BEB0"),
                         text_current_color=hex_color("#0C6170"))
        date_picker.bind(on_save=self.on_date_picker_save, on_cancel=self.on_date_picker_cancel)
        date_picker.open()

    def on_date_picker_save(self, instance, value, date_range):
        print(date_range)
        if not date_range:
            create_error_dialog("Invalid Date Range!", "Please pick a valid date range!")
            return -1
        self.formatted_date_range = []
        for item in date_range:
            self.formatted_date_range.append(datetime.strftime(item, "%d_%m_%Y"))
        self.ids.date_range_picker.font_size = "16sp"
        self.ids.date_range_picker.text = f"{self.formatted_date_range[0]} ---> {self.formatted_date_range[-1]}"

    def on_date_picker_cancel(self, instance, value):
        pass

    def create_subject_picker_menu(self):
        items = ["Foods Eaten", "Workouts", "Height/Weight"]

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": i,
                "height": dp(56),
                "on_release": lambda x=i: self.menu_callback(x),
            } for i in items
        ]
        self.subject_picker_menu = MDDropdownMenu(
            caller=self.ids.graph_subject_picker,
            items=menu_items,
            position="auto",
            width_mult=2.5,
        )

    def menu_callback(self, text_item):
        self.ids.graph_subject_picker.text = f"{text_item}"
        self.subject_picker_menu.dismiss()

    def get_graph_info(self, graph_subject):
        # dictionary to determine what document to access to retrieve data
        document = {
            "Foods Eaten": "user_foods",
            "Workouts": "user_workouts",
            "Height/Weight": "user_profile"
        }

        # check to see if a valid date range is provided
        if self.formatted_date_range:
            # try getting information from the database, using the document name and date range
            try:
                graph_info = database.get_info_for_graphs(document[graph_subject], self.formatted_date_range)
            # if the subject is not in the valid subjects (document dictionary) then create an error dialog
            except KeyError:
                create_error_dialog("Missing Input!", "Please choose a valid subject!")
                return -1
        # if the date range is invalid, then create an error dialog
        else:
            create_error_dialog("Missing Input!", "Please choose a valid date range!")
            return -1

        # if there is no graph info, then end the function
        if not graph_info:
            return -1

        # reformat item_list dicts
        for date_value, item_list in graph_info.items():
            # loop through all items for each day
            for item in item_list:
                # delete unnecessary fields (such as name, amount, Other)
                if graph_subject == "Foods Eaten":
                    # try deleting the following key value pairs
                    try:
                        del item["Other"], item["Name"], item["Amount"]
                    # if "Other" is not in the dictionary, then delete the other fields
                    except KeyError:
                        del item["Name"], item["Amount"]
                elif graph_subject == "Workouts":
                    del item["Exercise_Name"], item["MET"]
                elif graph_subject == "Height/Weight":
                    del item["Entry_Date"]

            # if the graph subject is for foods or workouts, then combine the dictionaries
            if graph_subject in ["Foods Eaten", "Workouts"]:
                combined_values = {}
                # for each key in each item
                for key in item_list[0].keys():
                    # take the sum of each value from that specific key (combining values from like keys)
                    combined_values[key] = sum(
                        float(value) for value in [item[key] if item[key] else 0 for item in item_list])
                # add new keys to combined_values dictionary
                graph_info[date_value] = combined_values
            # if the graph subject is height/weight, then format the data differently
            elif graph_subject == "Height/Weight":
                combined_dicts = {}
                # for each dictionary (inputted value)
                for dict in item_list:
                    # combine both dictionaries into 1, allowing for easier conversion for graphing
                    combined_dicts[list(dict.keys())[0]] = dict[list(dict.keys())[0]]
                # add to combined_dicts dictionary
                graph_info[date_value] = combined_dicts

        # format the dates into short, readable strings
        self.dates = []
        self.dates = [date_value[:5].replace("_", ":") for date_value in graph_info.keys()]

        # nutrient info for each stacked bar - nutrient1_all_days = [], nutrient2_all_days = [], ...

        # remove each swiper item from the display (if they exist)
        for swiper in self.ids.graph_swiper.get_items():
            self.ids.graph_swiper.remove_widget(swiper)

        # run a specific function to create each graph based on the subject
        if graph_subject == "Foods Eaten":
            self.add_food_graph(graph_info)
        elif graph_subject == "Workouts":
            self.add_workouts_graph(graph_info)
        elif graph_subject == "Height/Weight":
            self.add_height_weight_graph(graph_info)

    def add_food_graph(self, graph_info):
        self.graph_nutrients = {
            "Calories": [],
            "Carbohydrates": {"Carbohydrates": [], "Fibres": [], "Sugars": []},
            "Fat": {"Fat": [], "Saturated Fat": [], "Trans Fat": []},
            "Protein": [],
            "Vitamins": {"Cholesterol": [], "Sodium": [], "Potassium": [], "Vitamin A": [],
                         "Vitamin C": [], "Calcium": [], "Iron": []}
        }
        for combined_items in graph_info.values():
            for nutrient in combined_items.keys():
                if nutrient == "Calories":
                    self.graph_nutrients["Calories"].append(combined_items[nutrient])
                elif nutrient in ["Carbohydrates", "Fibres", "Sugars"]:
                    self.graph_nutrients["Carbohydrates"][nutrient].append(combined_items[nutrient])
                elif nutrient in ["Fat", "Saturated Fat", "Trans Fat"]:
                    self.graph_nutrients["Fat"][nutrient].append(combined_items[nutrient])
                elif nutrient == "Protein":
                    self.graph_nutrients["Protein"].append(combined_items[nutrient])
                elif nutrient in ["Cholesterol", "Sodium", "Potassium", "Vitamin A", "Vitamin C", "Calcium", "Iron"]:
                    self.graph_nutrients["Vitamins"][nutrient].append(combined_items[nutrient])

        # display graph
        for graph in self.graph_nutrients.keys():
            values, names = [], []
            try:
                for nutrient, value_list in self.graph_nutrients[graph].items():
                    values.append(value_list)
                    names.append(nutrient)
            except AttributeError:
                values.append(self.graph_nutrients[graph])
                names.append(graph)

            fig, ax = plt.subplots()

            fig.patch.set_facecolor("#DBF5F0")

            colors = ['#f8d0d9', '#db7a86', '#de4553', '#bb2d55', '#ae2f3a', '#8f001b', '#4c0012']

            for i in range(len(values)):
                ax.bar(self.dates, values[i], width=0.3, color=colors[i], label=names[i])

            ax.set_title(f"{graph} Graph")
            ax.legend()
            plt.xticks(rotation=45)

            try:
                self.ids.graph_swiper.add_widget(GraphSwiperItem(graph=FigureCanvasKivyAgg(plt.gcf())))
            except IndexError:
                self.ids.graph_swiper.add_widget(MDLabel(text="There was an error!/n/nPlease try again!",
                                                         halign="center"))

    def add_workouts_graph(self, graph_info):
        # dictionaries to store values for each graph (must be in list format)
        self.graph_workouts_stats = {
            "Burned Calories": [],
            "Duration": []
        }

        # add the statistic value for each date in the correct key in the graph_workouts_stats dictionary
        for combined_items in graph_info.values():
            for statistic in combined_items.keys():
                self.graph_workouts_stats[statistic.replace("_", " ")].append(combined_items[statistic])

        # for each graph key (which is 1 graph)
        for graph in self.graph_workouts_stats.keys():
            # make the values the list in the correct graph_workouts_stats
            values = [self.graph_workouts_stats[graph]]
            # create subplots for the figure and each section (bar)
            fig, ax = plt.subplots()
            # set the background color to baby blue
            fig.patch.set_facecolor("#DBF5F0")
            # make the colors of the bars shades of red
            colors = ["#bb2d55", '#de4553']

            # for each value in each list, add a new bar with date as the x-label, and the index in the values list
            for i in range(len(values)):
                ax.bar(self.dates, values[i], width=0.3, color=colors[i])

            # set the title to the key of the graph_workouts_stats dictionary
            ax.set_title(f"{graph} Graph")
            # make the x-labels titled, to conserve space
            plt.xticks(rotation=45)

            # try adding the graph
            try:
                # add a FigureCanvasKivyAgg widget as a swiper
                self.ids.graph_swiper.add_widget(GraphSwiperItem(graph=FigureCanvasKivyAgg(plt.gcf())))
            # if there is an error, then add a label, saying that it was unsuccessful
            except IndexError:
                self.ids.graph_swiper.add_widget(MDLabel(text="There was an error!/n/nPlease try again!",
                                                         halign="center"))

    def add_height_weight_graph(self, graph_info):
        print(graph_info)

        self.height_data, self.weight_date = {}, {}

        for date_value, combined_items in graph_info.items():
            if combined_items["Height"].strip().split(" ")[1] != "cm":
                combined_items["Height"] = float(combined_items["Height"].strip().split(" ")[0]) * 2.54
            else:
                combined_items["Height"] = float(combined_items["Height"].strip().split(" ")[0])

            if combined_items["Weight"].strip().split(" ")[1] != "kg":
                combined_items["Weight"] = float(combined_items["Weight"].strip().split(" ")[0]) * 0.453592
            else:
                combined_items["Weight"] = float(combined_items["Weight"].strip().split(" ")[0])

            self.height_data[date_value[:5].replace("_", ":")] = float(combined_items["Height"])
            self.weight_date[date_value[:5].replace("_", ":")] = float(combined_items["Weight"])
        print(self.height_data, self.weight_date)

        index = 0

        for data in [self.height_data, self.weight_date]:
            statistic = ["Height", "Weight"]
            fig, ax = plt.subplots()

            fig.patch.set_facecolor("#DBF5F0")

            # colors = ['#f8d0d9', '#db7a86', '#de4553', '#bb2d55', '#ae2f3a', '#8f001b', '#4c0012']
            colors = ["#bb2d55", '#de4553']

            ax.plot(list(data.keys()), list(data.values()))

            ax.set_title(f"{statistic[index]} Graph")
            plt.xticks(rotation=45)
            index += 1

            try:
                self.ids.graph_swiper.add_widget(GraphSwiperItem(graph=FigureCanvasKivyAgg(plt.gcf())))
            except IndexError:
                self.ids.graph_swiper.add_widget(MDLabel(text="There was an error!/n/nPlease try again!",
                                                         halign="center"))
        # print(self.graph_workouts_stats)
        #
        # dates = [date_value[:5].replace("_", ":") for date_value in self.formatted_date_range]
        #
        # print(x)

# Ben Williams '25, Sam Starrs '26
# April 2024
from matplotlib import animation

# For the logic of characteristics and preferences
from Person import Person

# For all plotting and graph making
import matplotlib.pyplot as plt
import networkx as nx

# To help with sorting the nodes
from operator import itemgetter

# For all randomization of interactions and people generation
import random

# For more efficient matrix and random operations
import numpy as np

# For analysis functions
import simulation_analysis_funcs

# To create directories and delete unwanted files
import os
import subprocess


# Allows us to close the plot on a timer - making it so you don't have to click to close plots
# This is a workaround to a networkx limitation
def close_plot_event():
    plt.close()


class Simulation:
    """
    min_friends - the minimum number of **max friends** an individual person might have. Default: 3
    max_friends - the maximum number of **max friends** an individual person might have. Default: 20
    num_people - the number of people who will be in the simulation. Default: 100
    min_interactions - The minimum number of interactions someone could have in a day. Default: 5
    max_interactions - The maximum number of interactions someone could have in a day. Default: 30
    """
    def __init__(self, min_friends=3, max_friends=20, num_people=100, min_interactions=5, max_interactions=30):

        ### Simulation parameters ###

        # Parameters for the Person objects
        self.min_friends = min_friends
        self.max_friends = max_friends
        self.num_people = num_people

        # The range for the number of interactions someone will have in a day
        self.min_interactions = min_interactions
        self.max_interactions = max_interactions

        # Influences how likely people are to hang out with friends and friends-of-friends
        self.direct_friend_weight = 10
        self.fof_weight = 2

        ### Initializations ###

        # We generate each person randomly. Their characteristics and preferences are randomly generated in Person.py
        self.people = [Person(random.randint(min_friends, max_friends), person) for person in range(num_people)]

        # Initialize friendship set of tuples (friend_id_1, friend_id_2)
        self.friendships = set()

        # Initialize array of unique friend groups over time
        self.avg_friends = []
        self.num_disjoint_groups = []
        self.avg_degrees_of_separation = []

        # Start between 0 and 0.8 for how much person_1 likes person_2 (consider this the personality modifier)
        initial_score_range = (0.3, 0.9)

        # Initialize the like scores matrix with shape (num_people, num_people)
        self.like_scores = self.__calculate_like_scores(initial_score_range)

    """
    Runs the simulation for the given number of days with the simulation's current status and parameters
    
    num_days - The number of days to run the simulation for
    show_each_day - Show a plot of each individual day
    show_video - Whether or not to show the video after it is created
    video_name - The name and output directory of the video to be created. If left empty, no video will be made
    
    """
    def run_simulation(self, num_days, video_name="", show_loners=False):
        image_paths = []

        for curr_day in range(num_days):
            self.simulate_day()

            friend_group_info = simulation_analysis_funcs.get_friend_group_info(sim)
            connectedness_info = simulation_analysis_funcs.get_connectedness_info(sim)

            self.avg_friends.append(connectedness_info["avg_friends"])
            self.num_disjoint_groups.append(friend_group_info["num_fgs"])
            self.avg_degrees_of_separation.append(connectedness_info["avg_avg_deg_sep"])

            if video_name:
                curr_day_str = ("0" * (5 - len(str(curr_day)) % 5)) + str(curr_day)
                img_path = f"img_{curr_day_str}.png"
                self.visualize_curr_friendships(show_graph=True, save_img_path=img_path, show_loners=show_loners)
                image_paths.append(img_path)

        if video_name:
            # Calls a child process to run the ffmpeg from the shell, creating the video from the frames
            subprocess.call([
                'ffmpeg', '-framerate', '3', '-i', 'img_%05d.png', '-r', '30', '-pix_fmt', 'yuv420p',
                video_name
            ])

            # Delete individual frames
            for img_path in image_paths:
                os.remove(img_path)

    # Simulates a day of people meeting each other
    # Return - Number of new friendships made
    def simulate_day(self):
        num_new_friendships = 0
        # leftover_people = []

        interaction_probs = self.__calculate_interaction_probabilities()
        # print(interaction_probs)
        
        # The number of interactions each person will have that day
        interactions_left = np.random.randint(low=self.min_interactions,
                                              high=self.max_interactions,
                                              size=self.num_people)

        # # Add all people that do not have the max number of friends
        # for person in range(self.num_people):
        #     if len(self.people[person].friends) < self.people[person].max_friends:
        #         leftover_people.append(person)

        # People who have interactions_left >= 1
        socializing_people = [i for i in range(self.num_people)]

        # We don't want to accidentally prioritize people with small IDs, so we shuffle
        interaction_order = [i for i in range(self.num_people)]
        random.shuffle(interaction_order)

        for person_idx in interaction_order:
            # They are the only person left still wanting to do anything...
            if len(socializing_people) == 1:
                break

            person = self.people[person_idx]

            # Skip this person if they've already met their max friends
            if len(person.friends) == person.max_friends:
                continue
            
            # How many more people will this person interact with today?
            num_interactions = interactions_left[person_idx]

            # Skip this person if they have already had their maximum interactions for the day
            if num_interactions == 0:
                continue

            # Randomly pick the people that this person will interact with based on their probabilities
            people_interacted_with = np.random.choice(a=self.people,
                                                      size=num_interactions,
                                                      p=interaction_probs[person_idx])

            # Loop through all people that they interact with
            for person_interacted_with in people_interacted_with:
                
                # Subtract the interaction from you
                interactions_left[person_idx] -= 1

                # person_idx wanted to hang out with the other person, but the other person was tired...
                if interactions_left[person_interacted_with.id] == 0:
                    continue

                # Both people hang out
                interactions_left[person_interacted_with.id] -= 1
                
                # If they are already friends, continue
                if (person_idx, person_interacted_with.id) in self.friendships:
                    continue
                if (person_interacted_with.id, person_idx) in self.friendships:
                    continue

                # They are not friends, so they could possibly become friends

                # Ensure neither party is at their max friend count
                if len(self.people[person_idx].friends) == self.people[person_idx].max_friends:
                    continue
                if len(person_interacted_with.friends) == person_interacted_with.max_friends:
                    continue

                # See if they like each other enough
                person_to_candidate_score = self.like_scores[person_idx][person_interacted_with.id]
                candidate_to_person_score = self.like_scores[person_interacted_with.id][person_idx]

                if person_to_candidate_score < person.friend_threshold:
                    continue

                if candidate_to_person_score < person_interacted_with.friend_threshold:
                    continue

                # If we've made it here, they like each other enough to become friends
                person.friends.append(person_interacted_with.id)
                person_interacted_with.friends.append(person_idx)

                self.friendships.add((person.id, person_interacted_with.id))
                num_new_friendships += 1
                # TODO: We could add stuff here to boost the likelihood that a person either meets their friend's
                #    friends or that they end up liking them

        return num_new_friendships

    # For each person, create a weighted probability distribution for how likely they are to interact with everyone else
    # For each common friend a person has with another, we add a bonus. For people who are already friends,
    #   we will add a larger bonus
    # The intended effect is that people will spend time with those that they already know, and are more likely
    #   to meet friends-of-friends than total strangers. This should make friend groups more likely to form
    def __calculate_interaction_probabilities(self):
        # Create the (num_people x num_people) matrix, weights start at one so people can meet strangers
        interaction_weights = np.ones((self.num_people, self.num_people))

        for person_idx in range(self.num_people):
            curr_person = self.people[person_idx]

            individual_interaction_weights = np.zeros(self.num_people)

            # Get all the people reachable in two steps (friend of a friend)
            #   Note: There may be repetitions and overlap with their direct friends
            # Also add direct-friend interaction weights
            reachable_in_two = np.zeros(self.num_people)
            for direct_friend_idx in curr_person.friends:
                # Add weight for being friends with this person
                individual_interaction_weights[direct_friend_idx] += self.direct_friend_weight

                # Find their friends-of-friends
                for friend_of_friend_idx in self.people[direct_friend_idx].friends:
                    reachable_in_two[friend_of_friend_idx] += 1

            # Add the friend-of-friend weights
            for fof_idx in range(self.num_people):
                individual_interaction_weights[fof_idx] += (reachable_in_two[fof_idx] * self.fof_weight)

            # Zero out this persons entry
            individual_interaction_weights[person_idx] = 0

            # Add the weights to the matrix
            interaction_weights[person_idx] += individual_interaction_weights

        # Normalize each row to be probabilities
        for row in range(self.num_people):
            total_weight = np.sum(interaction_weights[row])
            interaction_weights[row] /= total_weight

        return interaction_weights

    # Calculate how much everyone likes each other based off of their characteristics and preferences
    def __calculate_like_scores(self, initial_score_range):
        # Initialize like score matrix
        like_scores = [[0 for _ in range(self.num_people)] for _ in range(self.num_people)]

        # Loop through every possible person_1 --> person_2 connection
        for person_1 in range(self.num_people):
            for person_2 in range(self.num_people):
                # A person will not become friends with themselves
                if person_1 == person_2:
                    continue

                initial_score = random.uniform(initial_score_range[0], initial_score_range[1])

                # Get the actual Person objects
                person_1_obj = self.people[person_1]
                person_2_obj = self.people[person_2]

                # See how much person_1 prefers person_2's gender
                gender_modifier = person_1_obj.preferences["gender"][person_2_obj.characteristics["gender"]]

                # Subtract the age by 18 since the list index starts at 0
                age_modifier = person_1_obj.preferences["age"][person_2_obj.characteristics["age"] - 18]

                # See how much person_1 prefers person_2's race
                race_modifier = person_1_obj.preferences["race"][person_2_obj.characteristics["race"]]

                # See how much person_1 likes person_2's hobbies
                hobby_modifier = 0
                for hobby in person_2_obj.characteristics["hobbies"]:
                    hobby_modifier += person_1_obj.preferences["hobbies"][hobby]

                # The total score is the sum of the initial and all the modifiers
                total_like_score = initial_score + gender_modifier + age_modifier + race_modifier + hobby_modifier
                like_scores[person_1][person_2] = total_like_score

        return like_scores

    # Creates a Networkx graph and draws the friendships between people
    def visualize_curr_friendships(self, show_graph=True, show_loners=True, save_img_path=""):
        friendship_graph = nx.Graph()

        if show_loners:
            friendship_graph.add_nodes_from(range(self.num_people))
            friendship_graph.add_edges_from(self.friendships)
        else:
            friendship_graph.add_edges_from(self.friendships)

        # This allows us to get the most popular person and make them red
        node_and_degree = friendship_graph.degree()
        (largest_hub, degree) = sorted(node_and_degree, key=itemgetter(1))[-1]

        # print("---------\n", sorted(node_and_degree, key=itemgetter(1)))
        # Create ego graph of main hub
        # hub_ego = nx.ego_graph(friendship_graph, largest_hub)

        # The spring layout tries to spread nodes out as far as possible away from each other,
        #   and it makes isolated people easier to spot.
        pos = nx.spring_layout(friendship_graph)

        color_race_map = dict()
        color_race_map[0] = "#AA0000"
        color_race_map[1] = "#00AA00"
        color_race_map[2] = "#0000AA"
        color_race_map[3] = "#AA6600"
        color_race_map[4] = "#990099"
        color_race_map[5] = "#00AA66"

        colors = []
        for person in self.people:
            if not show_loners and len(person.friends) == 0:
                continue

            colors.append(color_race_map[person.characteristics["race"]])

        nx.draw(friendship_graph, pos, node_color=colors, node_size=50, with_labels=False)

        # Draw ego as large and red
        options = {"node_size": 150, "node_color": "#FF0000"}
        ego = nx.draw_networkx_nodes(friendship_graph, pos, nodelist=[largest_hub], **options)

        # nx.draw(friendship_graph)

        annot = plt.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == plt.gca():
                for node, (x, y) in pos.items():
                    contains = (x - event.xdata)**2 + (y - event.ydata)**2 <= 0.001
                    if contains:
                        ind = {"ind": [node]}
                        node = ind["ind"][0]
                        xy = pos[node]
                        annot.xy = xy
                        node_attr = self.__get_person_labels()[node]

                        annot.set_text(node_attr)
                        annot.set_visible(True)
                        plt.draw()
                        break
                    else:
                        if vis:
                            annot.set_visible(False)
                            plt.draw()

        plt.gcf().canvas.mpl_connect("motion_notify_event", hover)

        if save_img_path:
            plt.savefig(save_img_path)

        if show_graph:
            plt.show()
        else:
            # fig = plt.figure()
            # timer = fig.canvas.new_timer(
            #     interval=10)  # creating a timer object and setting an interval of 3000 milliseconds
            # timer.add_callback(close_plot_event)
            plt.show()

    def visualize_analysis(self):
        """
        Plot simulation results.
        """
        time_steps = list(range(1, len(self.num_disjoint_groups) + 1))

        # Plotting the number of disjoint friend groups over time
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, self.avg_friends, marker='o', color='b', label='Number of Friends')
        plt.xlabel('Time Steps')
        plt.ylabel('Average Number of Friends')
        plt.title('Average Number of Friends over Time')
        plt.legend()
        plt.grid(True)
        # plt.show()
        plt.savefig("avg_friends_over_time.png")

        # Plotting the number of disjoint friend groups over time
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, self.num_disjoint_groups, marker='o', color='b', label='Number of Friend Groups')
        plt.xlabel('Time Steps')
        plt.ylabel('Number of Unique Friend Groups')
        plt.title('Number of Disjoint Friend Groups Over Time')
        plt.legend()
        plt.grid(True)
        # plt.show()
        plt.savefig("disjoint_friend_groups_over_time.png")

        # Plotting the average degrees of separation over time
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, self.avg_degrees_of_separation, marker='o', color='r',
                 label='Average Degrees of Separation')
        plt.xlabel('Time Steps')
        plt.ylabel('Average Degrees of Separation')
        plt.title('Average Degrees of Separation Over Time')
        plt.legend()
        plt.grid(True)
        # plt.show()
        plt.savefig("avg_degrees_of_separation.png")

    # Gets the labels for each person based off of their __str__. As of now, doesn't really work.
    # We might want to redefine the __str__ method to have newlines.
    # Also: see https://stackoverflow.com/questions/61604636/adding-tooltip-for-nodes-in-python-networkx-graph
    def __get_person_labels(self):
        labels = dict()
        for person in range(len(self.people)):
            labels[person] = str(self.people[person])

        return labels

    def create_summary(self):
        with open("simulation_summary.txt", "w") as file:
            print("Simulation Summary:", file=file)
            for person in self.people:
                print(f"Person {person.id}:", file=file)
                print("\t", person, file=file)
                print("\tFriends:", person.friends, file=file)

    def create_analysis(self):
        with open("simulation_analysis.txt", "w") as file:
            i = 1
            print("Simulation Analysis:", file=file)
            print("\tAverage Number of Friends Over Time:", file=file)
            for number in self.avg_friends:
                print(f"\t\tDay {i}: {number}", file=file)
                i = i + 1
            print("\tUnique Friend Groups Over Time:", file=file)
            for number in self.num_disjoint_groups:
                print(f"\t\tDay {i}: {number}", file=file)
                i = i + 1
            i = 1
            print("\tAverage Degrees of Seperation Over Time:", file=file)
            for number in self.avg_degrees_of_separation:
                print(f"\t\tDay {i}: {number}", file=file)
                i = i + 1



if __name__ == "__main__":
    sim = Simulation(num_people=50, min_interactions=5, max_interactions=10)
    # for day in range(7):
    #     new_friends = sim.simulate_day()
    #     sim.visualize_curr_friendships(show_graph=True, save_img_path="graph.png")
    #     print(f"Simulated day {day}. {new_friends} new friendships made")
    #     # for person in sim.people:
    #     #     print(f'\tD{day} person {person.id}: has num friends {len(person.friends)}')

    sim.run_simulation(50, "50_days_50_people.mp4", show_loners=False)
    sim.visualize_analysis()
    sim.create_summary()
    sim.create_analysis()
    # print(sim.friendships)
    # sim.visualize_curr_friendships()

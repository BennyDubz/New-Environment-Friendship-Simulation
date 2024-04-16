# Ben Williams '25, Sam Starrs '26
# April 2024
import random


class Person:
    """
    max_friends - the maximum number of friends this person can have
    person_id - the id (integer) of the person
    characteristics - the age, gender, race, and hobbies of the person:
        age is in [18, 50] inclusive
        gender is in {0, 1}
        race is in {0, 1, 2, 3, 4, 5}
        hobbies is four numbers in {0, 1, ... , 18, 19}
    preferences - how much of a bonus or penalty does a person have for ages/genders/races/hobbies. Format below:
        preferences["age"] is a list of the bonus / penalty for a given age in [18, 50]
            so preferences["age"][30] would be the modifier for how much this person likes a 30-year-old
        all keys: "age", "gender", "race", "hobbies"

    Characteristics and preferences are randomly generated if none are given
    """

    def __init__(self, max_friends, person_id, characteristics=None, preferences=None):
        # May modify this later
        self.friend_threshold = random.uniform(0.5, 0.9)

        self.max_friends = max_friends
        self.id = person_id

        # Check if we are given pre-defined characteristics
        if not characteristics:
            self.characteristics = dict()
            self.__create_random_characteristics()
        else:
            self.characteristics = characteristics

        # Check if we are given pre-defined preferences
        if not preferences:
            self.preferences = self.__generate_random_preferences()
        else:
            self.preferences = preferences

        self.friends = []

    # Creates random characteristics for this person
    def __create_random_characteristics(self):
        self.characteristics = {
            "age":  random.randint(18, 50),  # Select a random age in {18, 50}
            "gender": random.randint(0, 1),  # Select a random gender in {0, 1}
            "race": random.randint(0, 5),  # Select a random race out of 6 options {0, 1, 2, 3, 4, 5}
            "hobbies": set(random.sample(range(20), 4)),  # Pick four hobbies out of twenty
        }

    # Creates random preferences for this person based on their characteristics
    def __generate_random_preferences(self):
        preferences = dict()

        # Age preferences
        same_age_pref = random.random() / 20  # bonus between 0 and 0.05 for same age
        age_diff_penalty = random.random() / 100  # penalty between 0 and 0.01 for each year of age difference
        preferences["age"] = [same_age_pref - abs(self.characteristics["age"] - age) * age_diff_penalty
                                   for age in range(18, 51)]

        # Gender preferences
        same_gender_pref = random.random() / 20  # bonus between 0 and 0.05 for same gender
        opposite_gender_pref = (random.random() / 10) - 0.05  # modifier between -0.05 and 0.05 for opposite gender
        preferences["gender"] = [same_gender_pref, opposite_gender_pref] \
            if self.characteristics["gender"] == 0 \
            else [opposite_gender_pref, same_gender_pref]

        # Race preferences
        same_race_pref = random.random() / 20  # bonus between 0 and 0.05 for same race
        other_race_pref = -random.random() / 20  # penalty between 0 and 0.05 for other race
        race_preferences = []
        for race in range(6):
            race_preferences.append(same_race_pref if self.characteristics["race"] == race else other_race_pref)
        preferences["race"] = race_preferences

        # Hobby Preferences
        similar_hobby_pref = random.random() / 20  # bonus between 0 and 0.05 for each common hobby
        hobby_preferences = []
        for hobby in range(20):
            hobby_preferences.append(similar_hobby_pref if hobby in self.characteristics["hobbies"] else 0)
        preferences["hobbies"] = hobby_preferences

        return preferences

    # A kind of lazy __str__ method. If we want to make good labels for people (on hover, ideally)
    #   then we could maybe adjust this to have newlines or whatever formatting is necessary. Alternatively,
    #   we can keep this and have a get_label() method.
    def __str__(self):
        return f"ID: {self.id} Num Friends: {len(self.friends)} Gender: {self.characteristics['gender']} " + \
               f"Age: {self.characteristics['age']} Race: {self.characteristics['race']}"

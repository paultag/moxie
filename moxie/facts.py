import random


def get_fact():
    return random.choice(FACTS)


def printable_fact(x):
    if len(x) > 80:
        return "{}\r\n{}".format(x[:80], printable_fact(x[80:]))
    return x


def get_printable_fact():
    return printable_fact(get_fact())


FACTS = [
    "The billionth digit of Pi is 9.",
    "Humans can survive underwater. But not for very long.",
    "A nanosecond lasts one billionth of a second.",
    "Honey does not spoil.",
    "The atomic weight of Germanium is seven two point six four.",
    "An ostrich's eye is bigger than its brain.",
    "Rats cannot throw up.",
    "Iguanas can stay underwater for twenty-eight point seven minutes.",
    "The moon orbits the Earth every 27.32 days.",
    "A gallon of water weighs 8.34 pounds.",
    "According to Norse legend, thunder god Thor's chariot was pulled across the sky by two goats.",
    "Tungsten has the highest melting point of any metal, at 3,410 degrees Celsius.",
    "Gently cleaning the tongue twice a day is the most effective way to fight bad breath.",
    "The Tariff Act of 1789, established to protect domestic manufacture, was the second statute ever enacted by the United States government.",
    "The value of Pi is the ratio of any circle's circumference to its diameter in Euclidean space.",
    "The Mexican-American War ended in 1848 with the signing of the Treaty of Guadalupe Hidalgo.",
    "In 1879, Sandford Fleming first proposed the adoption of worldwide standardized time zones at the Royal Canadian Institute.",
    "Marie Curie invented the theory of radioactivity, the treatment of radioactivity, and dying of radioactivity.",
    "At the end of The Seagull by Anton Chekhov, Konstantin kills himself.",
    "Hot water freezes quicker than cold water.",
    "The situation you are in is very dangerous.",
    "Polymerase I polypeptide A is a human gene. The shortened gene name is POLR1A",

    "The Sun is 330,330 times larger than Earth. The sun has approximately 333,000 times the mass of the Earth. In terms of volume it is 1.3 million times larger than the Earth.",
    "Dental floss has superb tensile strength. The tensile strength of dental floss depends on what it is made of. Nylon floss will have a much higher tensile strength than Teflon floss.",
    "Raseph, the Semitic god of war and plague, had a gazelle growing out of his forehead. The gazelle was part of a headdress and did not grow out of his head.",
    "Human tapeworms can grow up to twenty-two point nine meters. Some tapeworms can grow that long, but not the sort that infest humans.",
    "If you have trouble with simple counting, use the following mnemonic device: one comes before two comes before 60 comes after 12 comes before six trillion comes after 504. This will make your earlier counting difficulties seem like no big deal. While the mnemonic device itself is correct, it is very unlikely to enable a person to count.",
    "The first person to prove that cow's milk is drinkable was very, very thirsty. Adult humans in hunter-gatherer cultures are almost always lactose-intolerant; lactose-tolerance in adulthood has developed over time among people in agricultural societies where drinking milk is common (lactose-intolerance is common in Asians, whose agricultural societies never drank milk).",
    "Roman toothpaste was made with human urine. Urine as an ingredient in toothpaste continued to be used up until the 18th century. Urine has never been used as a toothpaste ingredient, but it was used as an ingredient in detergents and disinfectants from Roman times up until the 19th century.",
    "Volcano-ologists are experts in the study of volcanoes. \"Vulcanologists\" is more correct, but this is a valid alternative term.",
    "In Victorian England, a commoner was not allowed to look directly at the Queen, due to a belief at the time that the poor had the ability to steal thoughts. Science now believes that less than 4% of poor people are able to do this. Considering that 0% is less than 4%, this statement is technically true, though misleading.",

    "Cellular phones will not give you cancer. Only hepatitis.",
    "In Greek myth, Prometheus stole fire from the Gods and gave it to humankind. The jewelry he kept for himself.",
    "The Schrodinger's cat paradox outlines a situation in which a cat in a box must be considered, for all intents and purposes, simultaneously alive and dead. Schrodinger created this paradox as a justification for killing cats.",
    "In 1862, Abraham Lincoln signed the Emancipation Proclamation, freeing the slaves. Like everything he did, Lincoln freed the slaves while sleepwalking, and later had no memory of the event.",
    "The plural of surgeon general is surgeons general. The past tense of surgeons general is surgeonsed general",
    "Contrary to popular belief, the Eskimo does not have one hundred different words for snow. They do, however, have two hundred and thirty-four words for fudge.",
    "Halley's Comet can be viewed orbiting Earth every seventy-six years. For the other seventy-five, it retreats to the heart of the sun, where it hibernates undisturbed.",
    "The first commercial airline flight took to the air in 1914. Everyone involved screamed the entire way.",
    "Edmund Hillary, the first person to climb Mount Everest, did so accidentally while chasing a bird.",

    "We will both die because of your negligence.",
    "The Fact Sphere is a good person, whose insights are relevant.",
    "The Fact Sphere is a good sphere, with many friends.",
    "You will never go into space.",
    "Dreams are the subconscious mind's way of reminding people to go to school naked and have their teeth fall out.",

    "The square root of rope is string.",
    "89% of magic tricks are not magic. Technically, they are sorcery.",
    "At some point in their lives 1 in 6 children will be abducted by the Dutch.",
    "According to most advanced algorithms, the world's best name is Craig.",
    "To make a photocopier, simply photocopy a mirror.",
    "Whales are twice as intelligent, and three times as delicious, as humans.",
    "Pants were invented by sailors in the sixteenth century to avoid Poseidon's wrath. It was believed that the sight of naked sailors angered the sea god.",
    "In Greek myth, the craftsman Daedalus invented human flight so a group of Minotaurs would stop teasing him about it.",
    "The average life expectancy of a rhinoceros in captivity is 15 years.",
    "China produces the world's second largest crop of soybeans.",
    "In 1948, at the request of a dying boy, baseball legend Babe Ruth ate seventy-five hot dogs, then died of hot dog poisoning.",
    "William Shakespeare did not exist. His plays were masterminded in 1589 by Francis Bacon, who used a Ouija board to enslave play-writing ghosts.",
    "It is incorrectly noted that Thomas Edison invented 'push-ups' in 1878. Nikolai Tesla had in fact patented the activity three years earlier, under the name 'Tesla-cize'.",
    "The automobile brake was not invented until 1895. Before this, someone had to remain in the car at all times, driving in circles until passengers returned from their errands.",
    "The most poisonous fish in the world is the orange ruffy. Everything but its eyes are made of a deadly poison. The ruffy's eyes are composed of a less harmful, deadly poison.",
    "The occupation of court jester was invented accidentally, when a vassal's epilepsy was mistaken for capering.",
    "Before the Wright Brothers invented the airplane, anyone wanting to fly anywhere was required to eat 200 pounds of helium.",
    "Before the invention of scrambled eggs in 1912, the typical breakfast was either whole eggs still in the shell or scrambled rocks.",
    "During the Great Depression, the Tennessee Valley Authority outlawed pet rabbits, forcing many to hot glue-gun long ears onto their pet mice.",
    "This situation is hopeless.",
    "Diamonds are made when coal is put under intense pressure. Diamonds put under intense pressure become foam pellets, commonly used today as packing material. (Believe it or not, graphite put under intense pressure produces diamonds, not coal.)",
    "Corruption at 25%",
    "Corruption at 50% At the time you are holding the Fact Sphere, corruption is at 75%.",
    "Fact: Space does not exist.",
    "The Fact Sphere is not defective. Its facts are wholly accurate and very interesting.",
    "The Fact Sphere is always right.",

    "While the submarine is vastly superior to the boat in every way, over 97% of people still use boats for aquatic transportation. The second half of this fact is almost certainly true, but the first half is entirely subjective.",
    "The likelihood of you dying within the next five minutes is eighty-seven point six one percent.",
    "The likelihood of you dying violently within the next five minutes is eighty-seven point six one percent.",
    "You are about to get me killed. The game does not record the ultimate fate of the Fact Sphere.",
    "The Fact Sphere is the most intelligent sphere.",
    "The Fact Sphere is the most handsome sphere.",
    "The Fact Sphere is incredibly handsome.",
    "Spheres that insist on going into space are inferior to spheres that don't.",
    "Whoever wins this battle is clearly superior, and will earn the allegiance of the Fact Sphere.",
    "You could stand to lose a few pounds.",
    "Avocados have the highest fiber and calories of any fruit. Difficult to verify as it depends on your definition of fruit. Coconuts are almost pure cellulose fiber taken as a whole, but the edible part is quite low in fiber.",
    "Avocados have the highest fiber and calories of any fruit. They are found in Australians. The second half is true, although avocados can also be found in other places.",
    "Every square inch of the human body has 32 million bacteria on it. Difficult to verify as it could vary depending on whether you're counting the internal surfaces as well.",
    "The average adult body contains half a pound of salt. Depends on how you define \"salt\".",

    "Twelve. Twelve. Twelve. Twelve. Twelve. Twelve. Twelve. Twelve. Twelve. Twelve.",
    "Pens. Pens. Pens. Pens. Pens. Pens. Pens.",
    "Apples. Oranges. Pears. Plums. Kumquats. Tangerines. Lemons. Limes. Avocado. Tomato. Banana. Papaya. Guava.",
    "Error. Error. Error. File not found.",
    "Error. Error. Error. Fact not found.",
    "Fact not found.",
    "Warning, sphere corruption at twenty-- rats cannot throw up.",
]

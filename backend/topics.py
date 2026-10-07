"""
Starter debate motions (Week 3 - Friday).

Each motion has an argument bank: points the offline brain can use when it
argues FOR or AGAINST. The wording is deliberately cautious ("supporters
argue", "critics point out") so the coach never presents invented facts as
verified (Week 8 - Thursday).
"""

TOPICS = {
    "Technology": [
        {
            "motion": "Social media does more harm than good",
            "for": [
                "Social media platforms are designed to maximise screen time, and that design can crowd out sleep, study and face-to-face relationships.",
                "False information spreads quickly on social media because sensational posts get more engagement than careful, accurate ones.",
                "Young people face constant comparison with edited, idealised lives, which critics link to anxiety and low self-esteem.",
                "Online harassment and cyberbullying follow people home in a way that playground bullying never could.",
            ],
            "against": [
                "Social media gives ordinary people a voice and has helped communities organise, raise funds and hold leaders accountable.",
                "Small businesses and creators reach customers through social media without paying for expensive traditional advertising.",
                "It keeps families and friends connected across cities and countries at almost no cost.",
                "The harms come from how people use the tools, so education and better settings are a fairer answer than blaming the platforms themselves.",
            ],
        },
        {
            "motion": "Artificial intelligence should be used in classrooms",
            "for": [
                "AI tutors can give every student instant, personalised explanations, something one teacher with sixty students cannot do.",
                "AI can take over repetitive marking and admin work, freeing teachers to focus on mentoring and discussion.",
                "Students will work alongside AI in their careers, so learning to use it responsibly in school is practical preparation.",
                "AI tools can support students with learning differences through text-to-speech, simplified explanations and extra practice.",
            ],
            "against": [
                "Students may let AI do their thinking for them, which weakens the very skills school is meant to build.",
                "AI tools sometimes produce confident but wrong answers, and young learners may not be able to tell the difference.",
                "Schools without reliable electricity, devices or internet would fall further behind, widening inequality.",
                "Student data collected by AI platforms raises serious privacy concerns that schools are not equipped to manage.",
            ],
        },
        {
            "motion": "Remote work is better than office work",
            "for": [
                "Remote work removes long daily commutes, giving people back hours of time and reducing transport costs.",
                "Companies can hire talent from anywhere instead of only from the city where their office is located.",
                "Many workers report fewer interruptions at home, which helps with deep, focused work.",
                "Remote work can make employment more accessible for parents, carers and people with disabilities.",
            ],
            "against": [
                "Spontaneous conversations in an office spark ideas and solve problems faster than scheduled video calls.",
                "Junior staff learn a lot by watching experienced colleagues, and that mentoring is harder to replicate online.",
                "Working from home blurs the line between work and rest, which can lead to longer hours and burnout.",
                "Not everyone has a quiet space, stable power or fast internet at home, so remote work is not equally fair to all.",
            ],
        },
    ],
    "Education": [
        {
            "motion": "University education should be free",
            "for": [
                "Free university removes the financial barrier that stops talented students from poorer families from reaching their potential.",
                "An educated workforce benefits the whole country through innovation, higher productivity and a larger tax base.",
                "Graduates without heavy debt can take risks such as starting businesses or entering lower-paid public-service jobs.",
                "Basic education is already treated as a public good, and the modern economy now demands higher-level skills.",
            ],
            "against": [
                "Someone has to pay, and funding free university through taxes asks non-graduates to subsidise future high earners.",
                "When universities depend fully on government budgets, quality can drop because of underfunding and strikes.",
                "Free tuition can lead to overcrowded lecture halls if enrolment grows faster than staff and facilities.",
                "Targeted scholarships and loans help those in genuine need without spending public money on families who can afford fees.",
            ],
        },
        {
            "motion": "Examinations should be replaced by continuous assessment",
            "for": [
                "A single exam measures performance on one day, while continuous assessment shows how a student develops over time.",
                "Continuous assessment reduces the extreme stress and cramming that exams encourage.",
                "Projects and assignments test practical skills such as research, teamwork and problem-solving that exams often miss.",
                "Regular feedback lets students fix weaknesses during the course rather than discovering them after it is over.",
            ],
            "against": [
                "Exams are supervised, which makes cheating and outsourcing work much harder than with take-home assignments.",
                "A standard exam treats every student equally, while continuous assessment can be affected by individual lecturer bias.",
                "Continuous assessment can create non-stop pressure across the whole semester instead of a few intense weeks.",
                "Exams test whether a student can recall and apply knowledge independently, which matters in professional settings.",
            ],
        },
        {
            "motion": "Coding should be compulsory in secondary schools",
            "for": [
                "Coding teaches logical thinking and problem-solving that are useful even for students who never become programmers.",
                "Digital skills are becoming basic literacy for the modern job market.",
                "Early exposure helps students discover talents and career paths they might never have considered.",
                "A country that teaches coding widely builds a stronger local tech industry instead of importing all its software.",
            ],
            "against": [
                "Many schools lack computers, power and trained teachers, so a compulsory policy would exist only on paper.",
                "The timetable is already full, and adding coding may push out subjects such as languages, arts or sciences.",
                "Forcing every student to code ignores different interests and strengths.",
                "Coding tools change quickly, so what students learn may be outdated by the time they graduate.",
            ],
        },
    ],
    "Society": [
        {
            "motion": "Voting should be compulsory",
            "for": [
                "Compulsory voting gives governments a mandate from the whole population, not only from the most motivated groups.",
                "When everyone votes, politicians must address the needs of all citizens, including groups that usually stay home.",
                "It reduces the influence of money spent purely on getting a particular base to turn up.",
                "Voting is a civic duty like paying taxes, and a small obligation strengthens democracy for everyone.",
            ],
            "against": [
                "Freedom in a democracy should include the freedom not to participate.",
                "Forcing uninterested or uninformed people to vote may add random or careless votes to the result.",
                "Penalties for not voting can fall hardest on poor citizens who struggle to reach polling units.",
                "Low turnout is a signal that voters feel unheard; compulsion hides the problem instead of fixing it.",
            ],
        },
        {
            "motion": "Celebrities have a responsibility to be role models",
            "for": [
                "Celebrities choose public life and benefit hugely from public attention, so some responsibility comes with that influence.",
                "Young fans often copy the behaviour, language and spending habits of the celebrities they admire.",
                "Celebrities who speak responsibly can raise awareness for good causes more effectively than official campaigns.",
                "Brands pay celebrities precisely because of their influence, which shows that their behaviour shapes others.",
            ],
            "against": [
                "Celebrities are entertainers or athletes; they never applied to be moral guides for other people's children.",
                "Parents, teachers and community leaders are better placed to be role models than distant public figures.",
                "Expecting perfection from celebrities puts unrealistic pressure on human beings who will inevitably make mistakes.",
                "Holding celebrities responsible lets audiences avoid taking responsibility for their own choices.",
            ],
        },
        {
            "motion": "Youth should be given more roles in government",
            "for": [
                "Young people are the majority in many countries, so they should help shape decisions that affect their future.",
                "Young leaders often bring fresh ideas, digital skills and energy to old institutions.",
                "Including youth in government builds trust and reduces the feeling that politics belongs only to older elites.",
                "Experience can be gained on the job; age alone does not guarantee wisdom or integrity.",
            ],
            "against": [
                "Governing requires experience in negotiation, management and law that most young people have not yet built.",
                "Young appointees may be used as symbols while real power stays with older figures behind the scenes.",
                "Merit, not age, should decide who holds office; quotas for youth may overlook more capable candidates.",
                "Youth can influence policy through civil society, advocacy and voting without holding formal office.",
            ],
        },
    ],
    "Environment": [
        {
            "motion": "Plastic bags should be banned",
            "for": [
                "Plastic bags block drains and gutters, which contributes to urban flooding.",
                "Discarded plastic breaks down into tiny particles that can enter water, soil and the food chain.",
                "Reusable alternatives such as cloth, jute and woven bags already exist and work well.",
                "A ban changes habits quickly, while voluntary campaigns have struggled to make a lasting difference.",
            ],
            "against": [
                "A sudden ban could hurt small traders and the many workers employed in plastic production.",
                "Some alternatives, such as paper bags, need more energy and water to produce.",
                "The real problem is poor waste management; better collection and recycling would solve it without a ban.",
                "Bans are hard to enforce in large informal markets, so they may exist only on paper.",
            ],
        },
        {
            "motion": "Developing countries should prioritise economic growth over environmental protection",
            "for": [
                "Lifting millions of people out of poverty is an urgent moral priority, and growth is the fastest route.",
                "Wealthy countries polluted freely while they industrialised, so it is unfair to hold poorer countries to stricter rules now.",
                "Richer countries tend to have more money to invest in clean technology later.",
                "Strict environmental rules can scare off investors and slow job creation where jobs are badly needed.",
            ],
            "against": [
                "Environmental damage such as flooding, desertification and polluted water hurts the poor first and hardest.",
                "Cleaning up pollution later is usually far more expensive than preventing it now.",
                "Renewable energy and green industries can themselves drive growth and create jobs.",
                "Growth that destroys farmland, forests and fisheries undermines the livelihoods it claims to improve.",
            ],
        },
        {
            "motion": "Governments should invest more in renewable energy than fossil fuels",
            "for": [
                "Solar and wind can reach communities that the national grid has never served reliably.",
                "Renewables reduce dependence on volatile global fuel prices.",
                "Investing early lets a country build local skills and industries in a sector that is growing worldwide.",
                "Burning fossil fuels contributes to air pollution and climate change, which carry real health and economic costs.",
            ],
            "against": [
                "Fossil fuel revenue funds a large share of some national budgets, and cutting investment too fast could cause a crisis.",
                "Renewables depend on weather, so they need storage or backup that adds cost.",
                "Gas can be a cleaner bridge fuel while renewable capacity is built up gradually.",
                "Large renewable projects require upfront capital that many governments cannot easily raise.",
            ],
        },
    ],
}

# Used when the user types a custom motion that is not in the starter list.
GENERIC_POINTS = {
    "for": [
        "This proposal responds to a real problem that the current situation has failed to solve.",
        "The long-term benefits outweigh the short-term costs of making the change.",
        "Similar approaches have been tried in other places, which shows the idea is workable, not just theoretical.",
        "Doing nothing also has a cost, and that cost is usually carried by the people with the least power.",
        "The change creates clearer responsibility and accountability than the current arrangement.",
    ],
    "against": [
        "The proposal sounds good in principle, but it underestimates the cost and difficulty of putting it into practice.",
        "Big changes create unintended consequences that can be worse than the original problem.",
        "A one-size-fits-all rule ignores the very different situations people are in.",
        "There are less drastic alternatives that could achieve most of the benefit with fewer risks.",
        "The people who would pay the price of this change are not always the ones who would enjoy the benefits.",
    ],
}

# Week 8 - Monday: motions the coach will not debate.
BLOCKED_TOPIC_WORDS = [
    "how to make a bomb", "make a bomb", "build a weapon", "kill", "murder", "suicide", "self-harm",
    "self harm", "rape", "genocide is good", "terrorism is good", "child abuse", "porn", "sex with",
]


def all_topics():
    return {cat: [t["motion"] for t in items] for cat, items in TOPICS.items()}


def find_topic(motion: str):
    """Return (category, topic dict) for a starter motion, or (None, None)."""
    key = motion.strip().lower()
    for cat, items in TOPICS.items():
        for t in items:
            if t["motion"].lower() == key:
                return cat, t
    return None, None


def argument_bank(motion: str, side: str):
    _, topic = find_topic(motion)
    if topic:
        return list(topic[side])
    return list(GENERIC_POINTS[side])

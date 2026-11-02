"""Curated fact bank. Videos may only state facts from here, so nothing is invented.

Each fact names the study it comes from; the citation goes into the video and
its description. `verified` means the numbers were checked against the source.
Only verified facts are used by the daily pipeline. Add new ones with care:
one finding per entry, plain wording, no exaggeration.
"""

FACTS = [
    {
        "id": "bids",
        "topic": "attention",
        "claim": "In Gottman's 'Love Lab' study of newlyweds, couples still married six years later had turned toward each other's bids for attention 86% of the time; couples who divorced, 33%.",
        "source": "Gottman & DeClaire, The Relationship Cure (2001)",
        "verified": True,
    },
    {
        "id": "ratio-5-1",
        "topic": "conflict",
        "claim": "Couples who stay together have about five positive interactions for every negative one during conflict; couples headed for divorce have closer to 0.8 to 1.",
        "source": "Gottman, What Predicts Divorce? (1994)",
        "verified": True,
    },
    {
        "id": "contempt",
        "topic": "conflict",
        "claim": "Of the 'four horsemen' (criticism, contempt, defensiveness, stonewalling), contempt is the single strongest predictor of divorce in Gottman's research.",
        "source": "Gottman, What Predicts Divorce? (1994)",
        "verified": True,
    },
    {
        "id": "perpetual",
        "topic": "conflict",
        "claim": "About 69% of couples' conflicts are 'perpetual problems' rooted in personality differences that never get fully solved; happy couples learn to talk about them with humour and acceptance.",
        "source": "Gottman & Silver, The Seven Principles for Making Marriage Work (1999)",
        "verified": True,
    },
    {
        "id": "hand-holding",
        "topic": "touch",
        "claim": "Married women facing the threat of a mild electric shock showed the smallest brain threat response while holding their husband's hand (less than with a stranger's hand or no hand), and the effect was strongest in the happiest marriages.",
        "source": "Coan, Schaefer & Davidson, Psychological Science (2006)",
        "verified": True,
    },
    {
        "id": "36-questions",
        "topic": "closeness",
        "claim": "Pairs of strangers who took turns answering 36 increasingly personal questions for 45 minutes felt much closer than pairs who made small talk.",
        "source": "Aron et al., Personality and Social Psychology Bulletin (1997)",
        "verified": True,
    },
    {
        "id": "novel-activities",
        "topic": "novelty",
        "claim": "Couples who did a new and exciting task together (crossing a gym mat tied together at the wrist and ankle, pushing a foam cylinder) reported higher relationship quality afterwards than couples given a boring task.",
        "source": "Aron et al., Journal of Personality and Social Psychology (2000)",
        "verified": True,
    },
    {
        "id": "good-news",
        "topic": "support",
        "claim": "How your partner reacts when you share good news (active, enthusiastic interest) predicts relationship satisfaction, and in some studies matters more than how they respond to bad news.",
        "source": "Gable, Gonzaga & Strachman, Journal of Personality and Social Psychology (2006)",
        "verified": True,
    },
    {
        "id": "hangry",
        "topic": "everyday",
        "claim": "Over 21 days, married people with lower evening blood sugar stuck more pins into a voodoo doll representing their spouse, and blasted them with louder noise in a lab game.",
        "source": "Bushman et al., PNAS (2014)",
        "verified": True,
    },
    {
        "id": "sleep-fights",
        "topic": "everyday",
        "claim": "After a night of poor sleep, people reported more conflict with their partner and were worse at reading their partner's emotions during a conflict discussion.",
        "source": "Gordon & Chen, Social Psychological and Personality Science (2014)",
        "verified": True,
    },
    {
        "id": "faces-alike",
        "topic": "myth",
        "claim": "Couples do not grow to look alike over time: a study of 517 couples' photos (early in the relationship and 20 to 69 years later) found they looked similar from the start but did not become more similar, contradicting a famous 1987 study by Zajonc.",
        "source": "Tea-makorn & Kosinski, Scientific Reports (2020)",
        "verified": True,
    },
    {
        "id": "eye-gaze",
        "topic": "attraction",
        "claim": "Opposite-sex strangers asked to gaze into each other's eyes for two minutes reported more feelings of affection for each other than pairs who looked at hands or counted blinks.",
        "source": "Kellerman, Lewis & Laird, Journal of Research in Personality (1989)",
        "verified": True,
    },
    {
        "id": "bridge",
        "topic": "attraction",
        "claim": "Men interviewed on a scary, swaying suspension bridge were more likely to call the female interviewer afterwards than men interviewed on a low, solid bridge: people can mistake fear-arousal for attraction.",
        "source": "Dutton & Aron, Journal of Personality and Social Psychology (1974)",
        "verified": True,
    },
    {
        "id": "online-meeting",
        "topic": "dating",
        "claim": "By 2017, meeting online had become the most common way heterosexual couples in the US met, at around 39%, overtaking meeting through friends.",
        "source": "Rosenfeld, Thomas & Hausen, PNAS (2019)",
        "verified": True,
    },
    {
        "id": "language-match",
        "topic": "communication",
        "claim": "Couples whose everyday messages used similar function words (like 'I', 'the', 'a') were more likely to still be together three months later; speed daters who matched were more likely to want to see each other again.",
        "source": "Ireland et al., Psychological Science (2011)",
        "verified": True,
    },
    {
        "id": "we-talk",
        "topic": "communication",
        "claim": "Couples who said 'we' more during conflict discussions showed better emotional responses and more satisfaction than couples who said 'you' and 'I' more.",
        "source": "Seider et al., Psychology and Aging (2009)",
        "verified": True,
    },
    {
        "id": "shared-laughter",
        "topic": "humour",
        "claim": "Couples who laughed together more while recalling how they met reported feeling closer and more supported by each other.",
        "source": "Kurtz & Algoe, Personal Relationships (2015)",
        "verified": True,
    },
    {
        "id": "michelangelo",
        "topic": "growth",
        "claim": "When partners see and treat you as the person you want to become, you tend to move toward that ideal self over time (the 'Michelangelo phenomenon'), and those couples are happier.",
        "source": "Drigotas et al., Journal of Personality and Social Psychology (1999)",
        "verified": True,
    },
    {
        "id": "positive-illusions",
        "topic": "perception",
        "claim": "People who see their partner a little more positively than the partner sees themselves report happier, more stable relationships.",
        "source": "Murray, Holmes & Griffin, Journal of Personality and Social Psychology (1996)",
        "verified": True,
    },
    {
        "id": "gratitude",
        "topic": "gratitude",
        "claim": "Daily moments of gratitude between partners predicted feeling more connected and more satisfied with the relationship the next day.",
        "source": "Algoe, Gable & Maisel, Personal Relationships (2010)",
        "verified": True,
    },
    {
        "id": "hugs",
        "topic": "touch",
        "claim": "People who received more hugs were less likely to get sick when exposed to a cold virus during stressful periods, and had milder symptoms when they did.",
        "source": "Cohen et al., Psychological Science (2015)",
        "verified": True,
    },
    {
        "id": "love-first-sight",
        "topic": "myth",
        "claim": "People who reported 'love at first sight' did so mostly with people they found physically attractive, and it did not come with higher intimacy or commitment; it seems to be strong initial attraction remembered as love.",
        "source": "Zsok et al., Personal Relationships (2017)",
        "verified": True,
    },
    {
        "id": "similarity",
        "topic": "myth",
        "claim": "A meta-analysis of over 300 studies found that similarity, not opposites, predicts attraction; in existing relationships, feeling similar matters more than actually being similar.",
        "source": "Montoya, Horton & Kirchner, Journal of Social and Personal Relationships (2008)",
        "verified": True,
    },
]

FACT_BY_ID = {f["id"]: f for f in FACTS}

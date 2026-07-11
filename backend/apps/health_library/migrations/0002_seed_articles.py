from django.db import migrations
from django.utils.text import slugify


# Starter content per category. Informational only — no diagnosis or
# prescriptions (mirrors the chatbot's safety boundaries). Admins can edit,
# unpublish or add more via the Django admin.
ARTICLES = [
    ('MALARIA', 'Understanding Malaria',
     'What malaria is, how it spreads, and why prompt testing matters.',
     "Malaria is caused by parasites spread through the bite of infected Anopheles mosquitoes. "
     "Common signs include fever, chills, headache and body aches, often appearing 10–15 days after a bite.\n\n"
     "Malaria can become serious quickly, so anyone with a fever in a malaria-prone area should get a blood test "
     "as soon as possible. Only a health worker can confirm malaria and advise on treatment — do not self-treat."),
    ('MALARIA', 'Preventing Mosquito Bites',
     'Simple, proven steps to lower your risk of malaria at home.',
     "Sleeping under an insecticide-treated net every night is one of the most effective ways to prevent malaria. "
     "Clearing stagnant water around the home removes mosquito breeding sites.\n\n"
     "Wearing long sleeves in the evening and using screens on windows also helps. If you are pregnant or travelling "
     "to a high-risk area, ask a health worker what additional precautions are right for you."),

    ('DIABETES', 'Living Well with Diabetes',
     'Everyday habits that help keep blood sugar in a healthy range.',
     "Diabetes affects how your body manages blood sugar. Balanced meals, regular physical activity and taking any "
     "medication exactly as prescribed all help.\n\n"
     "Keeping regular clinic appointments lets your care team monitor your progress. Bring any questions about your "
     "readings or medication to a health worker — this article does not replace their advice."),
    ('DIABETES', 'Recognising Low Blood Sugar',
     'Common warning signs of hypoglycaemia and when to seek help.',
     "Low blood sugar (hypoglycaemia) can cause shakiness, sweating, confusion, or a fast heartbeat. It can come on "
     "quickly and needs attention.\n\n"
     "If you feel these symptoms, follow the plan your health worker gave you. If someone becomes very confused or "
     "loses consciousness, treat it as an emergency and seek medical help immediately."),

    ('HYPERTENSION', 'Understanding High Blood Pressure',
     'Why blood pressure matters and how it is monitored.',
     "High blood pressure (hypertension) often has no symptoms, which is why regular checks are important. Over time "
     "it can strain the heart and blood vessels.\n\n"
     "Reducing salt, staying active, and attending regular checks all support healthy blood pressure. A health worker "
     "can tell you what your numbers mean and whether any treatment is needed."),

    ('PREGNANCY', 'Antenatal Care Basics',
     'Why regular antenatal visits protect both mother and baby.',
     "Antenatal care means regular check-ups during pregnancy. These visits help monitor the health of both mother "
     "and baby and catch any concerns early.\n\n"
     "Eating well, resting, and attending every scheduled visit are important. Always discuss symptoms such as severe "
     "headaches, bleeding or reduced baby movement with a health worker without delay."),

    ('NUTRITION', 'Building a Balanced Plate',
     'A simple guide to combining foods for good nutrition.',
     "A balanced plate includes energy foods (like maize, rice or potatoes), body-building foods (like beans, eggs, "
     "fish or meat) and protective foods (fruits and vegetables).\n\n"
     "Drinking enough clean water and limiting very sugary or fatty foods supports overall health. For specific "
     "dietary needs, a health worker or nutritionist can give tailored guidance."),

    ('MENTAL_HEALTH', 'Looking After Your Mental Health',
     'Everyday ways to support your wellbeing and when to reach out.',
     "Mental health is part of overall health. Sleep, connection with others, physical activity and talking about "
     "your feelings all help.\n\n"
     "If low mood, worry or stress start to affect daily life, talking to someone you trust or a health worker can "
     "help. If you ever have thoughts of harming yourself, treat it as an emergency and seek help immediately."),

    ('CHILD_HEALTH', 'Caring for a Feverish Child',
     'General guidance on fever in children and warning signs.',
     "Fever is common in children and is often part of fighting an infection. Keep the child comfortable, offer "
     "plenty of fluids, and monitor how they are doing.\n\n"
     "Seek care promptly if a child is very young, the fever is high or persistent, or the child is unusually sleepy, "
     "not drinking, or having difficulty breathing. A health worker should guide any treatment."),

    ('VACCINATION', 'Why Childhood Vaccines Matter',
     'How routine immunisation protects children and communities.',
     "Vaccines help the body build protection against serious diseases before a child is exposed to them. Following "
     "the national immunisation schedule gives the best protection.\n\n"
     "Keep your child's vaccination card safe and attend appointments on time. If you miss a dose, a health worker "
     "can advise on catching up."),
]


def seed(apps, schema_editor):
    Article = apps.get_model('health_library', 'Article')
    for category, title, summary, content in ARTICLES:
        Article.objects.get_or_create(
            slug=slugify(title),
            defaults={
                'title': title,
                'category': category,
                'summary': summary,
                'content': content,
                'is_published': True,
            },
        )


def unseed(apps, schema_editor):
    Article = apps.get_model('health_library', 'Article')
    Article.objects.filter(slug__in=[slugify(t) for _, t, _, _ in ARTICLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('health_library', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]

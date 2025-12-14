from django.db import connection
from django.shortcuts import render
from .forms import GlobalSearchForm



def home_view(request):
    return render(request, "database/home.html")



def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def search_view(request):
    form = GlobalSearchForm(request.GET or None)
    q = ""
    results = []

    if form.is_valid():
        q = form.cleaned_data["q"].strip()

        # If empty, just show page
        if not q:
            return render(request, "database/search.html", {"form": form, "q": q, "results": results})

        name_prefix = f"{q}%"
        contains = f"%{q}%"
        q_upper = q.upper()

        # Detect IDs like R006, P003 (works even if you type r006 / p003)
        is_researcher_id = q_upper.startswith("R") and q_upper[1:].isdigit()
        is_research_id = q_upper.startswith("P") and q_upper[1:].isdigit()

        matches = []  # ✅ always defined

        # STEP 1: find matching researcher_ids and/or research_ids
        with connection.cursor() as cursor:
            if len(q) == 1:
                # ONLY name starts-with for single letter
                cursor.execute(
                    """
                    SELECT DISTINCT r.researcher_id, rd.research_id
                    FROM collecting_db r
                    LEFT JOIN research_data rd ON rd.researcher_id = r.researcher_id
                    WHERE r.name LIKE %s
                    """,
                    [name_prefix]
                )
                matches = cursor.fetchall()

            elif is_researcher_id:
                cursor.execute(
                    """
                    SELECT DISTINCT r.researcher_id, rd.research_id
                    FROM collecting_db r
                    LEFT JOIN research_data rd ON rd.researcher_id = r.researcher_id
                    WHERE r.researcher_id = %s
                    """,
                    [q_upper]
                )
                matches = cursor.fetchall()

            elif is_research_id:
                cursor.execute(
                    """
                    SELECT DISTINCT r.researcher_id, rd.research_id
                    FROM research_data rd
                    JOIN collecting_db r ON r.researcher_id = rd.researcher_id
                    WHERE rd.research_id = %s
                    """,
                    [q_upper]
                )
                matches = cursor.fetchall()

            else:
                cursor.execute(
                    """
                    SELECT DISTINCT r.researcher_id, rd.research_id
                    FROM collecting_db r
                    LEFT JOIN research_data rd ON rd.researcher_id = r.researcher_id
                    LEFT JOIN journals j ON j.journal_id = rd.journal_id
                    LEFT JOIN conferences c ON c.conference_id = rd.conference_id
                    LEFT JOIN linking_research_to_key_words lk ON lk.research_id = rd.research_id
                    LEFT JOIN keywords k ON k.word_id = lk.word_id
                    WHERE
                        r.name LIKE %s
                        OR rd.title LIKE %s
                        OR r.email LIKE %s
                        OR j.journal_name LIKE %s
                        OR c.conference_name LIKE %s
                        OR k.keyword LIKE %s
                    """,
                    [name_prefix, contains, contains, contains, contains, contains]
                )
                matches = cursor.fetchall()

        researcher_ids = sorted({row[0] for row in matches if row[0]})
        research_ids = sorted({row[1] for row in matches if row[1]})

        if researcher_ids or research_ids:
            where_parts = []
            params = []

            if researcher_ids:
                where_parts.append("r.researcher_id IN (" + ",".join(["%s"] * len(researcher_ids)) + ")")
                params.extend(researcher_ids)

            if research_ids:
                where_parts.append("rd.research_id IN (" + ",".join(["%s"] * len(research_ids)) + ")")
                params.extend(research_ids)

            where_sql = " OR ".join(where_parts)

            # STEP 2: fetch ALL related data for those IDs
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        r.researcher_id, r.name, r.affiliation, r.country, r.email, r.specialty,
                        rd.research_id, rd.title, rd.publication_date, rd.research_type,
                        j.journal_name,
                        c.conference_name,
                        GROUP_CONCAT(DISTINCT k.keyword ORDER BY k.keyword SEPARATOR ', ') AS keywords
                    FROM collecting_db r
                    LEFT JOIN research_data rd ON rd.researcher_id = r.researcher_id
                    LEFT JOIN journals j ON j.journal_id = rd.journal_id
                    LEFT JOIN conferences c ON c.conference_id = rd.conference_id
                    LEFT JOIN linking_research_to_key_words lk ON lk.research_id = rd.research_id
                    LEFT JOIN keywords k ON k.word_id = lk.word_id
                    WHERE {where_sql}
                    GROUP BY
                        r.researcher_id, r.name, r.affiliation, r.country, r.email, r.specialty,
                        rd.research_id, rd.title, rd.publication_date, rd.research_type,
                        j.journal_name, c.conference_name
                    ORDER BY r.name, rd.publication_date DESC
                    LIMIT 500;
                    """,
                    params
                )
                results = dictfetchall(cursor)

    return render(request, "database/search.html", {"form": form, "q": q, "results": results})

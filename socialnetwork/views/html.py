from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from socialnetwork import api
from socialnetwork.api import _get_social_network_user
from socialnetwork.models import SocialNetworkUsers
from socialnetwork.serializers import PostsSerializer

from fame.models import ExpertiseAreas, Fame, FameLevels


@require_http_methods(["GET"])
@login_required
def timeline(request):
    # using the serializer to get the data, then use JSON in the template!
    # avoids having to do the same thing twice

    # initialize community mode to False the first time in the session
    if 'community_mode' not in request.session:
        request.session['community_mode'] = False


    # get extra URL parameters:
    keyword = request.GET.get("search", "")
    published = request.GET.get("published", True)
    error = request.GET.get("error", None)

    # task 7
    user = _get_social_network_user(request.user)
    community_mode = request.session.get('community_mode', False)
    user_communities = list(user.communities.all())
    eligible_communities_ids = Fame.objects.filter(
        user=user, fame_level__numeric_value__gte=100).values_list('expertise_area', flat=True) 
    eligible_communities = ExpertiseAreas.objects.filter(
        id__in=eligible_communities_ids
    ).exclude(id__in=[c.id for c in user_communities])

    # if keyword is not empty, use search method of API:
    if keyword and keyword != "":
        context = {
            "posts": PostsSerializer(
                api.search(keyword, published=published), many=True
            ).data,
            "searchkeyword": keyword,
            "error": error,
            "followers": list(api.follows(_get_social_network_user(request.user)).values_list('id', flat=True)),
            "community_mode": community_mode,
            "user_communities": user_communities,
            "eligible_communities": eligible_communities,
        }
    else:  # otherwise, use timeline method of API:

        context = {
            "posts": PostsSerializer(
                api.timeline(
                    _get_social_network_user(request.user),
                    published=published,
                ),
                many=True,
            ).data,
            "searchkeyword": "",
            "error": error,
            "followers": list(api.follows(_get_social_network_user(request.user)).values_list('id', flat=True)),
            "community_mode": community_mode,
            "user_communities": user_communities,
            "eligible_communities": eligible_communities,
        }

    return render(request, "timeline.html", context=context)


@require_http_methods(["POST"])
@login_required
def follow(request):
    user = _get_social_network_user(request.user)
    user_to_follow = SocialNetworkUsers.objects.get(id=request.POST.get("user_id"))
    api.follow(user, user_to_follow)
    return redirect(reverse("sn:timeline"))


@require_http_methods(["POST"])
@login_required
def unfollow(request):
    user = _get_social_network_user(request.user)
    user_to_unfollow = SocialNetworkUsers.objects.get(id=request.POST.get("user_id"))
    api.unfollow(user, user_to_unfollow)
    return redirect(reverse("sn:timeline"))


@require_http_methods(["GET"])
@login_required
def bullshitters(request):
    results = api.bullshitters()
    return render(request, "bullshitters.html", {"results": results})

@require_http_methods(["POST"])
@login_required
def toggle_community_mode(request):
    request.session['community_mode'] = not request.session.get('community_mode', False)
    return redirect(reverse("sn:timeline"))

@require_http_methods(["POST"])
@login_required
def join_community(request):
    user = _get_social_network_user(request.user)
    community_id = request.POST.get("community_id")
    community = ExpertiseAreas.objects.get(id=community_id)
    print( "community")
    api.join_community(user, community)
    return redirect(reverse("sn:timeline"))

@require_http_methods(["POST"])
@login_required
def leave_community(request):
    user = _get_social_network_user(request.user)
    community_id = request.POST.get("community_id")
    community = ExpertiseAreas.objects.get(id=community_id)
    api.leave_community(user, community)
    return redirect(reverse("sn:timeline"))

@require_http_methods(["GET"])
@login_required
def similar_users(request):
    user = _get_social_network_user(request.user)
    similar = api.similar_users(user)
    return render(request, "similar_users.html", {"similar_users": similar})

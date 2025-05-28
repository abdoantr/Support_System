@login_required
@user_passes_test(is_technician)
def view_user_profile(request, user_id):
    """
    View for technicians to see customer profiles
    """
    # Get the user by ID
    user = get_object_or_404(User, id=user_id)
    
    # Get user tickets data
    user_tickets = Ticket.objects.filter(created_by=user)
    total_tickets = user_tickets.count()
    resolved_tickets = user_tickets.filter(status__in=["resolved", "closed"]).count()
    open_tickets = total_tickets - resolved_tickets
    
    # Get recent activities
    recent_tickets = user_tickets.order_by("-created_at")[:5]
    recent_comments = Comment.objects.filter(ticket__in=user_tickets, author=user).order_by("-created_at")[:5]
    
    context = {
        "viewed_user": user,  # The user being viewed
        "total_tickets": total_tickets,
        "resolved_tickets": resolved_tickets,
        "open_tickets": open_tickets,
        "recent_tickets": recent_tickets,
        "recent_comments": recent_comments,
        "is_customer_view": True,  # Flag to indicate this is a customer being viewed
    }
    
    return render(request, "users/profile.html", context)

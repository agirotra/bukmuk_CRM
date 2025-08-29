#!/usr/bin/env python3
"""
Demo script showing AI enrichment for individual library customers
"""

import pandas as pd
from data_cleaner import LeadsDataCleaner
import os

def demo_ai_enrichment():
    """Demonstrate AI enrichment for individual customers"""
    print("🤖 AI Enrichment Demo for Bumuk Library")
    print("=" * 50)
    
    # Sample individual customer data
    sample_leads = [
        {
            'full_name': 'Priya Sharma',
            'phone_number': '9876543210',
            'email': 'priya.sharma@email.com',
            'city': 'Mumbai',
            'child_age': '8 years',
            'lead_type': 'Parent with children'
        },
        {
            'full_name': 'Rahul Kumar',
            'phone_number': '8765432109',
            'email': 'rahul.kumar@email.com',
            'city': 'Delhi',
            'child_age': '15 years',
            'lead_type': 'Student'
        },
        {
            'full_name': 'Meera Patel',
            'phone_number': '7654321098',
            'email': 'meera.patel@email.com',
            'city': 'Bangalore',
            'child_age': '12 years',
            'lead_type': 'Parent with children'
        }
    ]
    
    print("📋 Sample Individual Customers:")
    for i, lead in enumerate(sample_leads, 1):
        print(f"\n{i}. {lead['full_name']}")
        print(f"   📱 {lead['phone_number']}")
        print(f"   📧 {lead['email']}")
        print(f"   🏙️ {lead['city']}")
        print(f"   👶 Child Age: {lead['child_age']}")
        print(f"   🏷️ Type: {lead['lead_type']}")
    
    print("\n" + "=" * 50)
    print("🤖 What AI Enrichment Would Analyze:")
    print("=" * 50)
    
    print("\n🎯 **Customer Segmentation:**")
    print("   • Priya Sharma → 'Parent with young children'")
    print("   • Rahul Kumar → 'High school student'")
    print("   • Meera Patel → 'Parent with pre-teen children'")
    
    print("\n💰 **Potential Value Assessment:**")
    print("   • Priya Sharma → HIGH (regular library user, family engagement)")
    print("   • Rahul Kumar → MEDIUM (student, study resources)")
    print("   • Meera Patel → HIGH (family activities, educational programs)")
    
    print("\n📚 **Engagement Strategy:**")
    print("   • Priya Sharma → 'Focus on children's programs, family reading events'")
    print("   • Rahul Kumar → 'Emphasize study spaces, academic resources, exam prep'")
    print("   • Meera Patel → 'Highlight educational activities, parent-child programs'")
    
    print("\n🎁 **Library Benefits to Highlight:**")
    print("   • Priya Sharma → ['Safe learning environment', 'Educational programs', 'Family activities']")
    print("   • Rahul Kumar → ['Quiet study spaces', 'Free textbooks', 'Research resources']")
    print("   • Meera Patel → ['Educational workshops', 'Family bonding activities', 'Academic support']")
    
    print("\n" + "=" * 50)
    print("💡 **How This Helps Your Library:**")
    print("=" * 50)
    
    print("\n1. **Personalized Marketing**")
    print("   • Send relevant program announcements to each customer type")
    print("   • Target parents with children's events")
    print("   • Offer study resources to students")
    
    print("\n2. **Better Customer Service**")
    print("   • Staff knows what to recommend to each customer")
    print("   • Personalized welcome messages")
    print("   • Relevant resource suggestions")
    
    print("\n3. **Program Development**")
    print("   • Understand what programs your customers want")
    print("   • Identify gaps in your offerings")
    print("   • Plan events based on customer segments")
    
    print("\n4. **Retention Strategies**")
    print("   • High-value customers get premium attention")
    print("   • At-risk customers get re-engagement campaigns")
    print("   • Personalized follow-up based on customer type")
    
    print("\n" + "=" * 50)
    print("🚀 **To Enable AI Enrichment:**")
    print("=" * 50)
    
    print("\n1. Get OpenAI API key from openai.com")
    print("2. Run: streamlit run crm_dashboard.py")
    print("3. Check 'Enable AI Enrichment' in sidebar")
    print("4. Enter your API key")
    print("5. Upload your leads file")
    print("6. Click 'Load & Process Data'")
    
    print("\n✨ AI will analyze all 188 leads and provide insights for each customer!")
    
    return True

if __name__ == "__main__":
    demo_ai_enrichment()

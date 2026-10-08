"""
Corpus Generator for FitZone Gym Knowledge Base (Assignment 2)
Generates 70 realistic, deeply detailed domain documents covering:
- Membership tiers & plans
- Group fitness classes
- Personal trainer bios & certifications
- Club rules & policies
- Facility zones & equipment
- Fee schedules & ancillary services
"""

from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "documents"

DOCUMENTS = [
    # ==========================================
    # 1. MEMBERSHIPS (12 Documents)
    # ==========================================
    (
        "MEM-01_basic_plan.md",
        """# FitZone Basic Membership Plan
- **Document ID**: MEM-01
- **Category**: Memberships
- **Target Audience**: Self-directed lifters and cardio enthusiasts
- **Last Revised**: September 2026

## Overview
The FitZone Basic Membership Plan is designed for members who prioritize independent workouts on the main gym floor without requiring instructor-led studio classes or personal coaching.

## Pricing and Terms
- **Monthly Dues**: Rs. 4,000 per month (billed on the 1st of each month).
- **Joining / Registration Fee**: Rs. 2,000 one-time fee upon initial enrollment.
- **Commitment Period**: Month-to-month, requiring no long-term lock-in contract.
- **Security Deposit**: None.

## Included Privileges
- Unlimited access to the main weight room floor, Olympic lifting platforms, and cardio mezzanine.
- Standard locker room access, including day lockers and hot showers.
- Complimentary initial fitness orientation with a fitness floor coach (30 minutes).
- Water bottle refilling stations across the facility.

## Exclusions & Restrictions
- Does **not** include group fitness classes (Yoga, HIIT, Zumba, Pilates, or Cycling).
- Does **not** include sauna, steam room, or recovery lounge access.
- Does **not** include complimentary guest passes.
- Access hours: Standard operating hours (6:00 AM - 11:00 PM weekdays; 8:00 AM - 10:00 PM weekends).
"""
    ),
    (
        "MEM-02_standard_plan.md",
        """# FitZone Standard Membership Plan
- **Document ID**: MEM-02
- **Category**: Memberships
- **Target Audience**: Regular gym-goers and group class participants
- **Last Revised**: September 2026

## Overview
The Standard Membership is FitZone's most popular tier, combining full access to strength and cardio facilities with unlimited participation in all group fitness classes.

## Pricing and Billing
- **Monthly Dues**: Rs. 6,000 per month.
- **Registration Fee**: Rs. 2,000 (waived during seasonal promotional drives).
- **Billing Frequency**: Auto-debit on the 1st or 15th of each calendar month.

## Included Privileges
- All privileges of the Basic Plan (full gym floor, free weights, cardio deck).
- **Unlimited Group Fitness Classes**: Access to over 40 weekly classes including Vinyasa Yoga, HIIT Cardio Burn, Strength & Conditioning, Mat Pilates, and Zumba.
- **Locker Amenities**: Daily towel service (one bath towel and one workout towel per visit).
- Priority online booking for high-demand class slots up to 72 hours in advance via the member portal.

## Exclusions
- Does not include one-on-one personal training sessions (available at additional hourly rates).
- Does not include private cryotherapy sessions or executive locker rentals.
"""
    ),
    (
        "MEM-03_premium_plan.md",
        """# FitZone Premium VIP Membership Plan
- **Document ID**: MEM-03
- **Category**: Memberships
- **Target Audience**: Comprehensive wellness seekers and athletes
- **Last Revised**: September 2026

## Overview
The FitZone Premium Membership represents our all-inclusive tier, bundling top-tier coaching, luxury spa amenities, and guest access.

## Pricing and Structure
- **Monthly Dues**: Rs. 9,000 per month.
- **Registration Fee**: Included / Free of charge.
- **Contract Duration**: 3-month initial commitment, transitioning to month-to-month thereafter.

## Included Benefits
- **Personal Training**: 4 complimentary 60-minute one-on-one personal training sessions per month with any Tier 1 or Tier 2 certified coach.
- **Spa & Wellness**: Unlimited access to the Himalayan salt sauna, eucalyptus steam room, and cold plunge tub.
- **Guest Privileges**: 2 complimentary guest passes per calendar month.
- **Body Composition**: 1 free quarterly InBody 570 clinical body composition scan with report review.
- **Apparel & Cafe Discount**: 10% discount on all purchases at the FuelBar Cafe and FitZone Pro Shop.
- Dedicated executive locker allocation with laundry service add-on eligibility.
"""
    ),
    (
        "MEM-04_annual_commitment_discount.md",
        """# FitZone Annual Commitment & Discount Policy
- **Document ID**: MEM-04
- **Category**: Memberships & Billing
- **Applicable Tiers**: Basic, Standard, and Premium
- **Last Revised**: September 2026

## Discount Structure
Members who commit to a 12-month annual upfront agreement receive a **15% total discount** off standard monthly rates:
- **Basic Annual**: Rs. 40,800 per year (equivalent to Rs. 3,400/mo, saving Rs. 7,200).
- **Standard Annual**: Rs. 61,200 per year (equivalent to Rs. 5,100/mo, saving Rs. 10,800).
- **Premium Annual**: Rs. 91,800 per year (equivalent to Rs. 7,650/mo, saving Rs. 16,200).

## Registration Fee Waiver
The standard one-time Rs. 2,000 registration fee is completely waived for all annual upfront contracts.

## Early Cancellation Rules on Annual Plans
Annual contracts may only be terminated early under verifiable medical incapacity (certified by a licensed physician) or permanent relocation outside a 25-kilometer radius. A 20% administrative recalculation penalty applies if terminated before 9 months.
"""
    ),
    (
        "MEM-05_student_membership.md",
        """# FitZone Student Membership Program
- **Document ID**: MEM-05
- **Category**: Memberships
- **Target Audience**: Enrolled college and university students
- **Last Revised**: September 2026

## Eligibility Requirements
- Valid, unexpired student photo identification card from a recognized educational institution.
- Minimum age requirement: 16 years of age (parental consent waiver required for members aged 16-17).

## Rates & Privileges
- **Discounted Rate**: Rs. 3,500 per month (equivalent to Standard Tier access at a 42% discount).
- **Registration Fee**: Discounted to Rs. 1,000.
- **Access Hours**: Monday to Friday: 9:00 AM – 4:00 PM and 8:30 PM – 11:00 PM; Weekends: Full hours (8:00 AM – 10:00 PM).
- **Class Access**: Includes free attendance in all off-peak group fitness classes.
- **Verification**: Student status must be re-verified every 6 months at the front reception.
"""
    ),
    (
        "MEM-06_corporate_wellness_plan.md",
        """# FitZone Corporate Wellness & Partner Plans
- **Document ID**: MEM-06
- **Category**: Memberships & Corporate Accounts
- **Target Audience**: Corporate organizations, law firms, software houses
- **Last Revised**: September 2026

## Corporate Tier Structure
- **Group 5-15 Employees**: 10% discount on Standard and Premium monthly rates.
- **Group 16-50 Employees**: 20% discount with waived registration fees for all participating staff.
- **Enterprise 50+ Employees**: Custom corporate retainer, quarterly on-site ergonomic workshops, and dedicated monthly billing invoicing.

## Corporate Account Administration
- Invoicing can be set to direct payroll deduction or direct corporate bank transfer.
- Participating employees must present an official corporate email address or employee identification badge during registration.
- Quarterly attendance and wellness engagement reports can be provided to HR administrators upon request.
"""
    ),
    (
        "MEM-07_senior_citizen_plan.md",
        """# FitZone Silver Fitness & Senior Citizen Membership
- **Document ID**: MEM-07
- **Category**: Memberships
- **Target Audience**: Adults aged 60 and above
- **Last Revised**: September 2026

## Program Overview
FitZone Silver Fitness is dedicated to active aging, mobility enhancement, fall prevention, and cardiovascular health for seniors aged 60+.

## Rates and Conditions
- **Monthly Fee**: Rs. 3,200 per month.
- **Registration Fee**: Waived.
- **Operating Hours Access**: Full access from 7:00 AM to 5:00 PM daily.

## Tailored Benefits
- Weekly attendance in dedicated "Senior Functional Mobility & Balance" classes.
- Complimentary quarterly blood pressure and heart rate monitoring check-ins with our on-staff physiotherapist.
- Guided equipment setup with certified fitness floor staff during every morning workout.
"""
    ),
    (
        "MEM-08_couples_family_package.md",
        """# FitZone Couples & Family Dual Membership
- **Document ID**: MEM-08
- **Category**: Memberships
- **Target Audience**: Spouses, domestic partners, and immediate family
- **Last Revised**: September 2026

## Plan Features & Rates
- **Dual Standard Plan**: Rs. 10,500/month for two partners (saves Rs. 1,500 compared to two individual Standard memberships).
- **Dual Premium Plan**: Rs. 16,000/month for two partners (saves Rs. 2,000 compared to individual Premium rates).
- **Child Add-On (Ages 14-17)**: Rs. 2,000/month per child with adult supervision mandatory during weight room usage.

## Policy Guidelines
Both primary and secondary members must reside at the same physical residential address. Payment must be processed through a single primary billing account.
"""
    ),
    (
        "MEM-09_off_peak_hours_pass.md",
        """# FitZone Off-Peak Flex Membership
- **Document ID**: MEM-09
- **Category**: Memberships
- **Target Audience**: Freelancers, shift workers, and midday gym enthusiasts
- **Last Revised**: September 2026

## Overview
The Off-Peak Pass provides full gym floor access during non-congested daytime hours at a substantial discount.

## Pricing & Permitted Hours
- **Monthly Dues**: Rs. 3,000 per month.
- **Allowed Access Windows**:
  - Weekdays: 10:00 AM to 4:00 PM (must badge in after 10:00 AM and exit by 4:00 PM).
  - Weekends: 1:00 PM to 6:00 PM.
- **Penalty for Off-Hour Badging**: Entry attempts outside designated off-peak windows will prompt a Rs. 500 single-visit surcharge at the turnstiles.
"""
    ),
    (
        "MEM-10_vip_executive_access.md",
        """# FitZone Black Card Executive Membership
- **Document ID**: MEM-10
- **Category**: Memberships
- **Target Audience**: C-suite executives and elite athletes
- **Last Revised**: September 2026

## Premium Amenities
- **Monthly Dues**: Rs. 15,000 per month.
- **Personal Locker**: Dedicated, assigned locker with personalized nameplate and keycard lock.
- **Daily Garment Care**: Complimentary daily workout laundry service (laundered and folded within 24 hours).
- **Personal Training**: 8 private 60-minute coaching sessions per month included.
- **Priority Recovery**: Unlimited access to the Cryotherapy chamber and NormaTec compression boots lounge.
- **Private Parking**: Reserved VIP parking stall right outside the main clubhouse entrance.
"""
    ),
    (
        "MEM-11_day_pass_and_trial_policy.md",
        """# FitZone Day Pass & Trial Visit Policy
- **Document ID**: MEM-11
- **Category**: Memberships & Front Desk
- **Target Audience**: Visitors, traveling athletes, prospective members
- **Last Revised**: September 2026

## 1-Day Complimentary Trial
- Prospective local residents are entitled to **one free 1-Day Trial Pass**.
- Requires presentation of a valid national identity card (CNIC) or driving license showing a local address.
- Prospective trials include access to the gym floor and one group fitness class (subject to capacity).

## Paid Single Day Pass
- **Standard Day Pass**: Rs. 1,000 per day. Provides full floor access and locker room usage.
- **VIP Day Pass**: Rs. 1,800 per day. Includes spa, sauna, and group class participation.
- If a day pass visitor registers for a monthly membership within 48 hours of their visit, the day pass fee is credited toward their first month's dues.
"""
    ),
    (
        "MEM-12_weekend_warrior_membership.md",
        """# FitZone Weekend Warrior Membership
- **Document ID**: MEM-12
- **Category**: Memberships
- **Target Audience**: Working professionals active primarily on weekends
- **Last Revised**: September 2026

## Specifics & Access Times
- **Monthly Dues**: Rs. 2,800 per month.
- **Permitted Days**: Friday 4:00 PM to Sunday 10:00 PM inclusive.
- **Facilities**: Complete access to strength floor, cardio equipment, and weekend group classes (Saturday Zumba, Sunday Morning Stretch).
- **Add-On Day Access**: Rs. 600 surcharge for single-day weekday admission.
"""
    ),

    # ==========================================
    # 2. GROUP CLASSES (15 Documents)
    # ==========================================
    (
        "CLS-01_vinyasa_yoga.md",
        """# FitZone Class Guide: Vinyasa Yoga Flow
- **Document ID**: CLS-01
- **Category**: Group Fitness Classes
- **Location**: Studio A (Mind & Body Studio)
- **Schedule**: Monday, Wednesday, Friday at 6:00 PM - 7:00 PM
- **Instructor**: Sarah Ali (500-hr RYT)

## Class Description
Vinyasa Yoga is a dynamic sequence linking breath with continuous fluid movement. Each session focuses on posture alignment, hip opening, core stability, and mindfulness, concluding with 10 minutes of guided Savasana meditation.

## Intensity & Suitability
- **Intensity Level**: Moderate (Level 2).
- Suitable for both beginners seeking flexibility and intermediate lifters needing active recovery.
- Yoga mats, yoga blocks, and resistance straps are provided sanitized inside Studio A.
- Participants must bring a sweat towel and water bottle. Barefoot or grip socks required.
"""
    ),
    (
        "CLS-02_yin_restorative_yoga.md",
        """# FitZone Class Guide: Yin & Restorative Yoga
- **Document ID**: CLS-02
- **Category**: Group Fitness Classes
- **Location**: Studio A
- **Schedule**: Sunday at 10:00 AM - 11:15 AM
- **Instructor**: Sarah Ali

## Class Description
A slow-paced, therapeutic style of yoga where passive floor postures are held for 3 to 5 minutes. Targets deep connective tissues, ligaments, joints, and deep fascia networks to release chronic tension accumulated from heavy resistance training.

## Recommended For
- Members experiencing lower back tightness, stiff hamstrings, or chronic desk fatigue.
- Ideal recovery protocol following heavy deadlifts and squats.
"""
    ),
    (
        "CLS-03_power_yoga_flow.md",
        """# FitZone Class Guide: Power Yoga & Core
- **Document ID**: CLS-03
- **Category**: Group Fitness Classes
- **Location**: Studio A
- **Schedule**: Tuesday & Thursday at 7:00 AM - 8:00 AM
- **Instructor**: Sarah Ali

## Class Description
An athletic, fast-tempo vinyasa style emphasizing muscular endurance, balance transitions (handstands, arm balances), and deep core engagement. Builds sweat quickly and elevates metabolic rate before the workday begins.
"""
    ),
    (
        "CLS-04_hiit_cardio_burn.md",
        """# FitZone Class Guide: HIIT Cardio Burn
- **Document ID**: CLS-04
- **Category**: Group Fitness Classes
- **Location**: Studio B (Performance Studio)
- **Schedule**: Tuesday and Thursday at 7:00 PM - 7:45 PM
- **Instructor**: Usman Malik (ACE Certified)

## Class Description
High-Intensity Interval Training combining bodyweight plyometrics, ski ergs, assault bikes, agility ladders, and battle ropes. Utilizes work-to-rest ratios of 40 seconds maximum exertion followed by 20 seconds active recovery across 6 intense circuits.

## Physiological Benefits
- Rapid calorie expenditure (up to 500-700 calories burned per 45-minute session).
- Enhances VO2 max and anaerobic threshold.
- Non-marking athletic training shoes and hydration are strictly mandatory.
"""
    ),
    (
        "CLS-05_hiit_tabata_intervals.md",
        """# FitZone Class Guide: Tabata Protocol Extreme
- **Document ID**: CLS-05
- **Category**: Group Fitness Classes
- **Location**: Studio B
- **Schedule**: Saturday at 11:00 AM - 11:45 AM
- **Instructor**: Usman Malik

## Class Description
Structured around the classic Izumi Tabata scientific timing protocol: 20 seconds of all-out ultra-high intensity followed by 10 seconds of complete rest, repeated for 8 continuous cycles (4 minutes per exercise station).

## Stations Include
- Sled pushes on artificial turf.
- Kettlebell swings (16kg - 24kg).
- RowErg sprint intervals.
- Medicine ball slams.
"""
    ),
    (
        "CLS-06_strength_and_conditioning.md",
        """# FitZone Class Guide: Strength & Conditioning
- **Document ID**: CLS-06
- **Category**: Group Fitness Classes
- **Location**: Weight Room Studio & Turf Zone
- **Schedule**: Monday and Wednesday at 8:00 PM - 9:00 PM
- **Instructor**: Ahmed Khan (CSCS Certified)

## Class Focus
Designed to build functional lean muscle, joint resilience, and explosive power. Incorporates barbell squats, trap bar deadlifts, dumbbell overhead presses, pull-ups, and farmer's carries under structured progressive overload templates.

## Safety & Equipment
- All participants are coached on barbell biomechanics and safe brace mechanics.
- Class is capped at 16 members to ensure personalized form correction by coach Ahmed.
"""
    ),
    (
        "CLS-07_olympic_weightlifting_fundamentals.md",
        """# FitZone Class Guide: Olympic Weightlifting Fundamentals
- **Document ID**: CLS-07
- **Category**: Group Fitness Classes
- **Location**: Olympic Lifting Platform Bay
- **Schedule**: Saturday at 9:00 AM - 10:30 AM
- **Instructor**: Ahmed Khan & Marcus Sterling

## Curriculum
Specialized clinic breaking down the Snatch and the Clean & Jerk into technical progressions. Utilizes wooden dowels, technique bars, and Eleiko bumper plates. Covers triple extension, bar path trajectory, and wrist/shoulder mobility.
"""
    ),
    (
        "CLS-08_zumba_cardio_dance.md",
        """# FitZone Class Guide: Zumba Cardio Dance Party
- **Document ID**: CLS-08
- **Category**: Group Fitness Classes
- **Location**: Studio A
- **Schedule**: Saturday at 5:00 PM - 6:00 PM & Tuesday at 6:00 PM - 7:00 PM
- **Instructor**: Nadia Parvez (Licensed Zumba Instructor)

## Class Highlights
An exhilarating, high-energy dance workout fusing Latin, Salsa, Merengue, and Afro-beat rhythms with cardiovascular conditioning. Designed for all fitness levels; no prior dancing background required.
"""
    ),
    (
        "CLS-09_mat_pilates_core.md",
        """# FitZone Class Guide: Mat Pilates & Core Stability
- **Document ID**: CLS-09
- **Category**: Group Fitness Classes
- **Location**: Studio A
- **Schedule**: Tuesday and Thursday at 11:00 AM - 12:00 PM
- **Instructor**: Elena Rostova (PMA Certified)

## Class Details
Low-impact conditioning focusing on the powerhouse core muscles (transversus abdominis, pelvic floor, multifidus). Enhances spinal alignment, pelvic stability, and muscular posture without joint impact.
"""
    ),
    (
        "CLS-10_reformer_pilates_studio.md",
        """# FitZone Class Guide: Reformer Pilates Semi-Private
- **Document ID**: CLS-10
- **Category**: Specialized Studio Classes
- **Location**: Private Reformer Suite (2nd Floor)
- **Schedule**: Daily by appointment (Slots available 8:00 AM - 8:00 PM)
- **Instructor**: Elena Rostova

## Class Format
Semi-private sessions utilizing Allegro 2 Reformer beds with carriage springs and pulley straps. Capped at 5 participants per session. Requires a supplementary class credit (Rs. 1,500 per session for Standard/Premium members).
"""
    ),
    (
        "CLS-11_spin_and_rhythm_cycling.md",
        """# FitZone Class Guide: Rhythm Cycle & Spin
- **Document ID**: CLS-11
- **Category**: Group Fitness Classes
- **Location**: Spin Theater (Sound & Light Enclosed Studio)
- **Schedule**: Monday, Wednesday, Friday at 7:00 AM - 7:45 AM & 6:30 PM - 7:15 PM
- **Instructor**: Tariq Vance & Guest Instructors

## Highlights
High-energy indoor cycling choreographed to pulse-pounding playlists with theater light sequencing. Uses Stages SC3 indoor bikes featuring dual SPD cleat pedals, magnetic resistance, and personal wattage console readouts.
"""
    ),
    (
        "CLS-12_boxing_and_kickboxing_conditioning.md",
        """# FitZone Class Guide: Boxing Conditioning & Bag Work
- **Document ID**: CLS-12
- **Category**: Group Fitness Classes
- **Location**: Combat Zone & Heavy Bag Ring
- **Schedule**: Monday, Wednesday at 5:00 PM - 6:00 PM
- **Instructor**: Tariq Vance (Former Golden Gloves Competitor)

## Structure
Non-contact striking workout combining heavy bag combinations, slip-line footwork, shadowboxing, and core medicine ball circuits. Hand wraps and 14oz/16oz boxing gloves are mandatory (rentals available at front desk for Rs. 200).
"""
    ),
    (
        "CLS-13_kettlebell_functional_movement.md",
        """# FitZone Class Guide: Hardstyle Kettlebell Conditioning
- **Document ID**: CLS-13
- **Category**: Group Fitness Classes
- **Location**: Functional Turf Zone
- **Schedule**: Thursday at 6:00 PM - 7:00 PM
- **Instructor**: Farhan Qureshi (StrongFirst SFG I)

## Class Curriculum
Mastery of the six core kettlebell movements: The Swing, Clean, Military Press, Front Squat, Snatch, and Turkish Get-Up. Teaches explosive hip hinge mechanics, lat engagement, and breathing under tension.
"""
    ),
    (
        "CLS-14_senior_mobility_and_balance.md",
        """# FitZone Class Guide: Senior Functional Mobility
- **Document ID**: CLS-14
- **Category**: Group Fitness Classes
- **Location**: Studio A
- **Schedule**: Monday and Thursday at 9:30 AM - 10:30 AM
- **Instructor**: Dr. Zoya Merchant (DPT) & Sarah Ali

## Class Focus
Gentle joint mobilization, chair-assisted balance drills, light resistance band exercises, and gait stability exercises tailored to maintain independence and joint health in adults over 60.
"""
    ),
    (
        "CLS-15_aqua_fitness_and_swimming_clinic.md",
        """# FitZone Class Guide: Aqua Aerobics & Hydro Conditioning
- **Document ID**: CLS-15
- **Category**: Group Fitness Classes
- **Location**: Indoor Heated Lap Pool
- **Schedule**: Tuesday and Thursday at 8:30 AM - 9:30 AM
- **Instructor**: Coach Bilal Butt

## Details
Zero-impact cardiovascular conditioning in our 25-meter temperature-controlled indoor pool. Utilizes hydro foam dumbbells and water resistance kickboards to challenge muscles without spinal loading.
"""
    ),

    # ==========================================
    # 3. PERSONAL TRAINERS (10 Documents)
    # ==========================================
    (
        "TRN-01_ahmed_khan_strength.md",
        """# FitZone Trainer Profile: Ahmed Khan
- **Document ID**: TRN-01
- **Category**: Personal Trainers & Coaching
- **Designation**: Head Strength & Hypertrophy Coach
- **Experience**: 8+ Years

## Credentials & Certifications
- Certified Strength & Conditioning Specialist (CSCS - NSCA).
- Precision Nutrition Level 1 (PN1) Certified.
- National Powerlifting Championship Bronze Medalist (2021).

## Specializations
- Hypertrophy (muscle gain) periodization and program design.
- Powerlifting technique (Squat, Bench, Deadlift mechanics).
- Post-injury return-to-lift strength progressions.

## Individual Coaching Rates
- **Single Session**: Rs. 2,500 / 60 minutes.
- **10-Session Block**: Rs. 22,000 (saves Rs. 3,000).
- Availability: Monday to Friday: 2:00 PM – 9:00 PM; Saturday: 9:00 AM – 2:00 PM.
"""
    ),
    (
        "TRN-02_sarah_ali_yoga_mobility.md",
        """# FitZone Trainer Profile: Sarah Ali
- **Document ID**: TRN-02
- **Category**: Personal Trainers & Coaching
- **Designation**: Lead Yoga & Functional Mobility Specialist
- **Experience**: 6+ Years

## Credentials & Certifications
- 500-hour Registered Yoga Teacher (RYT-500, Yoga Alliance).
- Functional Range Conditioning (FRC) Mobility Specialist.
- Mat & Reformer Pilates Certified (Balanced Body).

## Specializations
- Postural restoration and anterior pelvic tilt correction.
- Deep hip and thoracic spine mobility for athletes.
- Breathwork and somatic nervous system down-regulation.

## Private Rates
- **Single 1-on-1 Session**: Rs. 2,200 / 60 minutes.
- **12-Session Mobility Transformation Package**: Rs. 23,000.
"""
    ),
    (
        "TRN-03_usman_malik_hiit_functional.md",
        """# FitZone Trainer Profile: Usman Malik
- **Document ID**: TRN-03
- **Category**: Personal Trainers & Coaching
- **Designation**: Performance & Metabolic Conditioning Coach
- **Experience**: 5+ Years

## Credentials & Certifications
- American Council on Exercise (ACE) Certified Personal Trainer.
- EXOS Fitness Specialist (XFS).
- CPR/AED Certified Instructor.

## Specializations
- Rapid metabolic fat loss through interval training.
- Athletic agility, jump mechanics, and sprint conditioning.
- Functional movement screen (FMS) assessments.

## Coaching Rates
- **Single Session**: Rs. 2,000 / 60 minutes.
- **10-Session HIIT Conditioning Package**: Rs. 18,000.
"""
    ),
    (
        "TRN-04_tariq_vance_boxing_conditioning.md",
        """# FitZone Trainer Profile: Tariq Vance
- **Document ID**: TRN-04
- **Category**: Personal Trainers & Coaching
- **Designation**: Combat Sports & Cycling Conditioning Specialist
- **Experience**: 7+ Years

## Background & Certifications
- USA Boxing Certified Coach & Former Amateur Fighter.
- Schwinn Cycling Certified Master Instructor.
- NASM Performance Enhancement Specialist (PES).

## Focus Areas
- Pad work, mitt holding, striking defense, and footwork drills.
- High-intensity anaerobic threshold development for endurance athletes.
- Private 1-on-1 boxing mitt work: Rs. 2,400 per hour.
"""
    ),
    (
        "TRN-05_dr_zoya_merchant_physical_therapy.md",
        """# FitZone Specialist Profile: Dr. Zoya Merchant (DPT)
- **Document ID**: TRN-05
- **Category**: Rehabilitation & Physical Therapy
- **Designation**: On-Site Doctor of Physical Therapy
- **Experience**: 9+ Years Clinical Experience

## Qualifications
- Doctor of Physical Therapy (DPT).
- Certified Dry Needling & Manual Therapy Practitioner.
- Specialist in orthopedic assessment and spinal mechanics.

## Services Offered
- Orthopedic injury assessment and musculoskeletal evaluations.
- Post-surgical rehabilitation protocols.
- Assisted active stretching and therapeutic manual muscle release.
- **Consultation Rate**: Rs. 3,500 (Initial 60-min Assessment); Follow-ups: Rs. 2,500 (45 mins).
"""
    ),
    (
        "TRN-06_elena_rostova_pilates_posture.md",
        """# FitZone Trainer Profile: Elena Rostova
- **Document ID**: TRN-06
- **Category**: Personal Trainers & Coaching
- **Designation**: Master Pilates Reformer & Spine Specialist
- **Experience**: 10+ Years International Coaching

## Certifications
- PMA Certified Pilates Teacher.
- Comprehensive apparatus qualification (Cadillac, Chair, Reformer).
- Core stability and prenatal rehabilitation certified.

## Private Reformer Rates
- **1-on-1 Private Reformer Session**: Rs. 3,000 / 60 minutes.
- **5-Session Private Block**: Rs. 13,500.
"""
    ),
    (
        "TRN-07_marcus_sterling_powerlifting.md",
        """# FitZone Trainer Profile: Marcus Sterling
- **Document ID**: TRN-07
- **Category**: Personal Trainers & Coaching
- **Designation**: Elite Powerlifting & Strength Coach
- **Experience**: 7+ Years

## Credentials
- USAPL Certified Club Coach.
- Westside Barbell Special Strengths Certified.
- Mentored over 30 competitive powerlifting medalists.

## Focus
Maximal strength output, heavy bar path diagnostics, meet prep peaking, and belt/wrap optimization. Single session: Rs. 2,500.
"""
    ),
    (
        "TRN-08_bilal_butt_youth_athletics.md",
        """# FitZone Trainer Profile: Bilal Butt
- **Document ID**: TRN-08
- **Category**: Personal Trainers & Coaching
- **Designation**: Youth Athletics & Aquatic Specialist
- **Experience**: 4+ Years

## Certifications
- ASCA Level 2 Swimming Coach.
- Youth Fitness Specialist (ISSA).
- Red Cross Certified Water Safety Instructor (WSI).

## Services
- Private swim stroke clinics for adults and teens.
- Youth athletic coordination and foundational speed development.
"""
    ),
    (
        "TRN-09_aisha_noor_prenatal_postnatal.md",
        """# FitZone Specialist Profile: Aisha Noor
- **Document ID**: TRN-09
- **Category**: Women's Health & Coaching
- **Designation**: Pre & Postnatal Exercise Specialist
- **Experience**: 6+ Years

## Qualifications
- Pre & Postnatal Fitness Specialist (GGS / Girls Gone Strong).
- Pelvic Floor & Core Rehab Coach.
- Diastasis recti assessment and recovery specialist.
- Offers safe strength workouts across all pregnancy trimesters and postpartum phases.
"""
    ),
    (
        "TRN-10_farhan_qureshi_tactical_kettlebell.md",
        """# FitZone Trainer Profile: Farhan Qureshi
- **Document ID**: TRN-10
- **Category**: Functional Strength
- **Designation**: StrongFirst Certified Kettlebell Instructor (SFG I & II)
- **Experience**: 6+ Years

## Focus
Tactical fitness, grip endurance, asymmetric loading, and military physical readiness test preparation. Private session: Rs. 2,200.
"""
    ),

    # ==========================================
    # 4. CLUB POLICIES & RULES (15 Documents)
    # ==========================================
    (
        "POL-01_membership_freeze_and_pause.md",
        """# FitZone Policy: Membership Freeze & Pause Guidelines
- **Document ID**: POL-01
- **Category**: Club Policies
- **Applies To**: All active paying members
- **Last Revised**: September 2026

## Allowable Freeze Duration
- Members in good financial standing are eligible to freeze their membership for a maximum of **30 cumulative days per calendar year**.
- Freezes must be requested in minimum increments of **7 consecutive days**.

## Notice & Submission Requirements
- An advance written notice of at least **48 hours** is strictly required prior to the requested freeze start date.
- Requests must be submitted via the online Member Portal or signed in person at the front reception desk. Verbal requests or phone messages are not accepted.

## Fees & Exceptions
- Standard annual and 6-month contracts: **Freeze is 100% free of charge**.
- Month-to-month memberships: Incur a nominal maintenance fee of **Rs. 500 per 30-day freeze cycle**.
- **Medical Freeze Exception**: If a member provides an official medical note from a licensed doctor certifying injury, pregnancy bed-rest, or surgery, the freeze may be extended up to **90 days** with all maintenance fees waived.
"""
    ),
    (
        "POL-02_cancellation_and_termination.md",
        """# FitZone Policy: Membership Cancellation & Termination
- **Document ID**: POL-02
- **Category**: Club Policies
- **Applies To**: Month-to-month and term memberships
- **Last Revised**: September 2026

## Notice Period
- Cancellation requests require a minimum of **7 days written notice** prior to the next scheduled monthly billing date (the 1st or 15th).
- If notice is received less than 7 days prior to billing, the upcoming month's dues will be processed, and membership will terminate at the conclusion of that following cycle.

## Procedure
- Cancellation forms must be submitted through the Member Portal under Account Settings or signed directly at the member services desk.
- Outstanding account balances, unpaid cafe tabs, or locker key replacement fees must be settled prior to account closure.

## Termination of Term Contracts
- Term contracts (such as 12-month commitments) terminated prematurely without qualifying relocation or medical grounds incur a cancellation fee equal to 1 month's standard dues.
"""
    ),
    (
        "POL-03_guest_pass_privileges.md",
        """# FitZone Policy: Guest Pass & Visitor Privileges
- **Document ID**: POL-03
- **Category**: Club Policies
- **Applies To**: Standard and Premium Members
- **Last Revised**: September 2026

## Allocation Rules
- **Premium Members**: Receive **2 complimentary guest passes per calendar month**. Unused passes do not roll over to subsequent months.
- **Standard Members**: May purchase discounted guest passes at **Rs. 600 per visit** (normal day pass rate is Rs. 1,000).

## Guest Requirements
- All guests must be at least 18 years of age (or 16+ accompanied by an adult legal guardian).
- Every guest must present valid government photo identification (CNIC / Passport) and sign our Liability Release Waiver at the front desk prior to entering the gym floor.
- The hosting member must remain on the gym premises for the duration of the guest's visit.
"""
    ),
    (
        "POL-04_locker_rental_and_day_use.md",
        """# FitZone Policy: Locker Rentals & Day Use Lockers
- **Document ID**: POL-04
- **Category**: Amenities & Policies
- **Last Revised**: September 2026

## Day Use Lockers
- Day lockers are provided free of charge to all members during their workout.
- Members must provide their own padlock or purchase a combination lock at the front desk for Rs. 500.
- All day lockers must be emptied before facility closing each evening. Locks left overnight will be clipped at 11:15 PM by security, and contents placed in Lost & Found.

## Permanent Locker Rentals
- Executive permanent lockers can be rented for a fee of **Rs. 1,500 per month** (subject to waitlist availability).
- Premium members receive a 20% discount on permanent locker rentals.
"""
    ),
    (
        "POL-05_sauna_steam_room_etiquette.md",
        """# FitZone Policy: Sauna & Eucalyptus Steam Room Etiquette
- **Document ID**: POL-05
- **Category**: Wellness Amenities
- **Last Revised**: September 2026

## Health & Safety Guidelines
- Users must shower with soap prior to entering the sauna or steam rooms.
- Clean towels must be placed between the user and wooden benches at all times for hygiene.
- Maximum recommended duration: 15 consecutive minutes per session.
- Individuals with uncontrolled high blood pressure, cardiac conditions, or who are pregnant are advised against heat exposure without prior medical clearance.
- Footwear: Rubber sandals or flip-flops must be worn when walking into the wet spa area.
"""
    ),
    (
        "POL-06_swimming_pool_and_jacuzzi_rules.md",
        """# FitZone Policy: Swimming Pool & Jacuzzi Regulations
- **Document ID**: POL-06
- **Category**: Aquatic Amenities
- **Last Revised**: September 2026

## Rules of Conduct
- Proper swimwear is required (nylon/spandex swimming trunks, one-piece or athletic two-piece swimsuits). Cotton gym shirts and denim shorts are strictly prohibited in the water.
- Silicon or latex swim caps are mandatory for all swimmers with hair past shoulder length.
- Dedicated circle swimming protocol applies in designated fast and medium lap lanes.
- No diving into the shallow end (minimum depth: 1.2m; maximum depth: 2.2m).
"""
    ),
    (
        "POL-07_dress_code_and_footwear.md",
        """# FitZone Policy: Apparel & Footwear Regulations
- **Document ID**: POL-07
- **Category**: Floor Safety
- **Last Revised**: September 2026

## Mandatory Attire
- Clean athletic tops (t-shirts, tank tops, compression shirts) covering the chest must be worn on all gym floors.
- Closed-toe, athletic footwear with non-marking rubber soles is strictly required across the strength and cardio zones.
- **Prohibited Footwear**: Sandals, slides, flip-flops, work boots, dress shoes, and bare feet are strictly disallowed on the strength floor.
- Exception: Deadlifting in socks or barefoot is permitted strictly on rubber deadlift platforms with shoes replaced immediately after the set.
"""
    ),
    (
        "POL-08_age_limits_and_minor_access.md",
        """# FitZone Policy: Age Restrictions & Minor Access
- **Document ID**: POL-08
- **Category**: Safety & Eligibility
- **Last Revised**: September 2026

## Age Tiers
- **Ages 18 and Above**: Full independent access without restrictions.
- **Ages 16 – 17**: Eligible for standard membership upon completion of a mandatory fitness orientation and signed parental consent form.
- **Ages 14 – 15**: May train under direct, active supervision of an adult member parent or legal guardian. Restricted from free barbell benches and heavy deadlift platforms.
- **Under Age 14**: Not permitted on fitness floors or in studio classes under any circumstances due to safety regulations.
"""
    ),
    (
        "POL-09_lost_and_found_procedure.md",
        """# FitZone Policy: Lost and Found Property Procedure
- **Document ID**: POL-09
- **Category**: Security & Guest Services
- **Last Revised**: September 2026

## Storage & Retrieval
- Items found on gym floors or in locker rooms are logged daily in the security incident register at the front desk.
- **High-Value Items** (smartphones, smartwatches, jewelry, wallets, wireless earbuds): Stored inside the reception safe for up to 60 days. Must present matching ID or unlock passcodes to claim.
- **Clothing & Water Bottles**: Stored in sanitized bins for 14 days. Unclaimed clothing items are donated to local charitable shelters bi-weekly.
"""
    ),
    (
        "POL-10_cell_phone_photography_privacy.md",
        """# FitZone Policy: Photography, Filming & Privacy
- **Document ID**: POL-10
- **Category**: Member Privacy
- **Last Revised**: September 2026

## Privacy Standards
- **Zero Tolerance in Locker Rooms**: Mobile phone camera usage, photography, and video calls are strictly illegal and prohibited in all locker rooms, showers, saunas, and restrooms. Violations lead to immediate membership revocation.
- **Floor Filming**: Filming personal workout sets on the gym floor is permissible only when using compact tripods that do not obstruct walkways and provided other members are not recorded without consent.
"""
    ),
    (
        "POL-11_code_of_conduct_and_zero_tolerance.md",
        """# FitZone Policy: Member Code of Conduct
- **Document ID**: POL-11
- **Category**: Community Standards
- **Last Revised**: September 2026

## Rules of Respect
- **Weights Re-Racking**: All weight plates, dumbbells, barbells, and attachments must be returned to their designated storage trees and racks immediately after use.
- **Equipment Sharing**: During peak hours (6:00 PM - 9:00 PM), members must allow others to "work in" between sets on resistance machines.
- **Aggressive Behavior**: Verbal abuse, physical intimidation, harassment, or unauthorized commercial personal training will result in immediate permanent expulsion.
"""
    ),
    (
        "POL-12_sanitation_hygiene_towel_policy.md",
        """# FitZone Policy: Equipment Sanitation & Towels
- **Document ID**: POL-12
- **Category**: Health & Sanitation
- **Last Revised**: September 2026

## Guidelines
- Members must wipe down each piece of equipment, cardio console, and bench with provided antibacterial spray and disposable paper towels after each exercise set.
- Bringing a personal sweat towel is mandatory for every workout session.
- Members exhibiting fever, contagious respiratory illness, or open wounds are requested to refrain from facility use until fully cleared.
"""
    ),
    (
        "POL-13_medical_clearance_and_waivers.md",
        """# FitZone Policy: Health Screening & Medical Clearance
- **Document ID**: POL-13
- **Category**: Risk & Compliance
- **Last Revised**: September 2026

## Physical Activity Readiness (PAR-Q)
All joining members must complete the standard PAR-Q questionnaire. Any affirmative response regarding cardiovascular symptoms, unexplained dizziness, or joint pain requires a signed medical clearance form from a physician prior to facility usage.
"""
    ),
    (
        "POL-14_parking_facility_regulations.md",
        """# FitZone Policy: Parking Facility Regulations
- **Document ID**: POL-14
- **Category**: Facilities
- **Last Revised**: September 2026

## Parking Rules
- Complimentary parking is available for up to **3 consecutive hours** per visit in the basement and surface lot.
- Members must scan their membership card at the exit validation kiosk before returning to their vehicle.
- Overnight parking is strictly prohibited without prior authorization; unauthorized vehicles will be towed at owner's expense after 12:00 midnight.
"""
    ),
    (
        "POL-15_emergency_and_incident_reporting.md",
        """# FitZone Policy: Emergency Protocols & First Aid
- **Document ID**: POL-15
- **Category**: Safety & First Aid
- **Last Revised**: September 2026

## Emergency Readiness
- Automated External Defibrillators (AEDs) are stationed on Ground Floor (by reception) and 1st Floor (by cardio deck).
- All senior shift managers and trainers are certified in adult CPR and AED operation.
- In case of medical emergency, members must notify staff immediately by pressing the red wall-mounted intercom buttons located across the floor.
"""
    ),

    # ==========================================
    # 5. FACILITIES & EQUIPMENT (8 Documents)
    # ==========================================
    (
        "FAC-01_free_weights_and_olympic_zone.md",
        """# FitZone Facility: Free Weights & Olympic Bay
- **Document ID**: FAC-01
- **Category**: Facilities & Equipment
- **Floor**: Ground Floor
- **Last Revised**: September 2026

## Specifications & Equipment
- **Dumbbell Array**: 4 complete sets ranging from 2.5 kg up to 60 kg (urethane-encased).
- **Barbells**: 12 Texas Power Bars, 4 Eleiko Olympic Competition Bars, 2 Safety Squat Bars, and 2 Trap/Hex Bars.
- **Platforms**: 6 drop-rated Olympic hardwood platforms with sound-dampening rubber perimeter tiles.
- **Benches**: 8 adjustable incline/decline benches and 4 competition flat benches with safety catches.
- Chalk bowls with magnesium carbonate chalk provided beside all Olympic platforms.
"""
    ),
    (
        "FAC-02_cardio_deck_and_endurance_suite.md",
        """# FitZone Facility: Cardio Mezzanine & Endurance Suite
- **Document ID**: FAC-02
- **Category**: Facilities & Equipment
- **Floor**: 1st Floor Mezzanine
- **Last Revised**: September 2026

## Machines Available
- 16 Life Fitness Elevation Series Treadmills with high-definition virtual running courses.
- 10 Concept2 RowErgs and 4 Concept2 SkiErgs.
- 8 StairMaster 8-Series Gauntlets (Stair Climbers).
- 6 Keiser M3i Indoor Cycle Ergometers with magnetic resistance.
- 6 Precor Adaptive Motion Trainers (AMT).
- Cardio entertainment: Integrated Bluetooth audio pairing for personal smartphones and individual streaming screens.
"""
    ),
    (
        "FAC-03_functional_turf_and_calisthenics.md",
        """# FitZone Facility: Functional Turf & Calisthenics Rig
- **Document ID**: FAC-03
- **Category**: Facilities & Equipment
- **Floor**: Ground Floor East Wing
- **Last Revised**: September 2026

## Equipment Lineup
- 30-meter high-density sprint turf track.
- 2 heavy-duty Rogue Dog Sleds with push poles and harness attachments.
- Modular calisthenics rig with pull-up stations, gymnastics rings, and dip bars.
- Plyometric jump boxes (12", 20", 24", 30" soft foam and wooden variants).
- 50-foot poly dacron battle ropes and Romanian wall-ball rebound targets.
"""
    ),
    (
        "FAC-04_recovery_lounge_and_cryotherapy.md",
        """# FitZone Facility: Recovery Lounge & Cryo Center
- **Document ID**: FAC-04
- **Category**: Facilities & Wellness
- **Floor**: 2nd Floor Spa Annex
- **Last Revised**: September 2026

## Recovery Amenities
- **Whole-Body Cryotherapy Chamber**: Cold vapor therapy (-110°C) for 3-minute recovery cycles.
- **NormaTec 3 Compression Suites**: Dynamic pneumatic compression boots for accelerated lower body lymphatic drainage.
- **Theragun Percussive Therapy Bar**: Access to Theragun PRO massage devices.
- **Infrared Sauna**: Full spectrum infrared wavelengths promoting circulation and muscle soothing.
"""
    ),
    (
        "FAC-05_juice_bar_and_nutrition_cafe.md",
        """# FitZone Facility: FuelBar Nutrition Cafe
- **Document ID**: FAC-05
- **Category**: Food & Nutrition Services
- **Location**: Lobby Area
- **Hours**: 6:30 AM – 10:00 PM Daily
- **Last Revised**: September 2026

## Offerings
- Handcrafted whey and plant-based protein shakes with custom macronutrient profiling.
- Cold-pressed organic green juices, electrolyte hydration drinks, and pre-workout espresso shots.
- High-protein ready-to-eat wraps, oats bowls, and Greek yogurt parfaits.
- Members can link their cafe account to their membership keycard for cashless tap-and-go billing.
"""
    ),
    (
        "FAC-06_pro_shop_and_apparel_store.md",
        """# FitZone Facility: Pro Shop & Apparel
- **Document ID**: FAC-06
- **Category**: Retail Services
- **Location**: Adjacent to Front Desk
- **Hours**: 8:00 AM – 9:00 PM Daily
- **Last Revised**: September 2026

## Merchandise
- FitZone official branded performance gym shirts, hoodies, training shorts, and gym bags.
- Lifting accessories: Harbinger weightlifting belts, wrist wraps, lifting straps, and knee sleeves.
- Certified nutritional supplements: Optimum Nutrition Gold Standard Whey, Creatine Monohydrate, and BCAAs.
"""
    ),
    (
        "FAC-07_luxury_showers_and_grooming_suites.md",
        """# FitZone Facility: Locker Rooms & Grooming Suites
- **Document ID**: FAC-07
- **Category**: Facilities
- **Last Revised**: September 2026

## Highlights
- Individual marble rain showers with organic shampoo, conditioner, and body wash dispensers.
- High-velocity Dyson Supersonic hair dryers and lighted vanity grooming mirrors.
- Complimentary grooming essentials including shaving cream, cotton pads, hair ties, and antiperspirant spray.
- Continuous cleaning protocol: Dedicated janitorial staff stationed full-time in locker suites.
"""
    ),
    (
        "FAC-08_ada_accessibility_and_amenities.md",
        """# FitZone Facility: Accessibility & Inclusive Design
- **Document ID**: FAC-08
- **Category**: Accessibility & Inclusion
- **Last Revised**: September 2026

## Features
- Dedicated ADA elevator providing ramp-free access to the 1st floor cardio deck and 2nd floor studio suites.
- Wheelchair-accessible roll-in showers and widened turnstile access gates.
- Certified wheelchair-compatible cable stations and upper body ergometers (arm cycles).
"""
    ),

    # ==========================================
    # 6. FEES, BILLING & ADD-ONS (10 Documents)
    # ==========================================
    (
        "FEE-01_registration_and_administrative_fees.md",
        """# FitZone Schedule: Registration & Admin Fees
- **Document ID**: FEE-01
- **Category**: Billing & Fees
- **Last Revised**: September 2026

## Fee Schedule
- **Standard Registration Fee**: Rs. 2,000 (one-time fee at enrollment).
- **RFID Membership Access Keycard**: First card is free; replacement of lost keycard is Rs. 500.
- **Account Transfer Fee**: Transferring an active term membership to a family member or friend incurs a Rs. 1,000 processing fee.
- **Payment Method Update**: Free through Member Portal.
"""
    ),
    (
        "FEE-02_personal_training_package_rates.md",
        """# FitZone Schedule: Personal Training Rates & Bundles
- **Document ID**: FEE-02
- **Category**: Coaching Rates
- **Last Revised**: September 2026

## Tier 1 Coaches (Junior / Associate Trainers)
- Single Session: Rs. 1,800
- 10-Session Bundle: Rs. 16,000 (saves Rs. 2,000)
- 20-Session Bundle: Rs. 29,000 (saves Rs. 7,000)

## Tier 2 Coaches (Senior Specialists — e.g., Ahmed Khan, Sarah Ali)
- Single Session: Rs. 2,500
- 10-Session Bundle: Rs. 22,000 (saves Rs. 3,000)
- 20-Session Bundle: Rs. 40,000 (saves Rs. 10,000)

## Expiration Terms
All 10-session packages are valid for 90 days from the purchase date. 20-session packages are valid for 180 days.
"""
    ),
    (
        "FEE-03_inbody_scan_and_body_composition.md",
        """# FitZone Service: InBody 570 Body Composition Analysis
- **Document ID**: FEE-03
- **Category**: Diagnostic Services
- **Last Revised**: September 2026

## Test Details & Rates
- **InBody 570 Clinical Test**: Rs. 1,200 per scan for non-members and Basic members.
- **Standard Members**: Discounted rate of Rs. 800 per scan.
- **Premium Members**: One free scan included every quarter (90 days).
- **Metrics Measured**: Skeletal muscle mass (SMM), percent body fat (PBF), visceral fat grade, intracellular water, and segmental lean analysis.
- Includes a 15-minute consultation review with a certified trainer.
"""
    ),
    (
        "FEE-04_nutrition_counseling_and_meal_plans.md",
        """# FitZone Service: Nutrition Counseling & Meal Plans
- **Document ID**: FEE-04
- **Category**: Nutrition Services
- **Last Revised**: September 2026

## Service Packages
- **Single Nutritional Consultation (45 mins)**: Rs. 2,500. Evaluates current food log, macronutrient splits, and metabolic demands.
- **4-Week Structured Transformation Meal Plan**: Rs. 6,000. Includes weekly check-ins, grocery shopping guides, and recipe adjustments.
- **8-Week Athletic Peaking Nutrition Program**: Rs. 10,500.
"""
    ),
    (
        "FEE-05_swimming_lane_rental_and_coaching.md",
        """# FitZone Service: Pool Lane Reservation & Private Swim
- **Document ID**: FEE-05
- **Category**: Aquatics & Rates
- **Last Revised**: September 2026

## Rates
- **Private Lap Lane Reservation (60 mins)**: Rs. 1,500 (guaranteed exclusive single lane for interval swimming).
- **Private 1-on-1 Adult Swim Coaching**: Rs. 2,000 per 45-minute lesson with Coach Bilal Butt.
- **Package of 8 Swim Lessons**: Rs. 14,000.
"""
    ),
    (
        "FEE-06_private_studio_rental_rates.md",
        """# FitZone Service: Private Studio Rental for Instructors
- **Document ID**: FEE-06
- **Category**: Facility Rentals
- **Last Revised**: September 2026

## Studio Rental Fees
- **Studio A (Mind & Body - 1,200 sq ft)**: Rs. 3,500 per hour (includes sound system and dimmable lighting).
- **Studio B (HIIT / Turf - 1,500 sq ft)**: Rs. 4,500 per hour (includes timer monitors and audio setup).
- Available during off-peak windows only (11:00 AM – 4:00 PM weekdays). Must carry independent liability insurance.
"""
    ),
    (
        "FEE-07_late_payment_and_dishonor_charges.md",
        """# FitZone Policy: Late Payment & Collection Penalties
- **Document ID**: FEE-07
- **Category**: Billing & Accounting
- **Last Revised**: September 2026

## Grace Period & Fees
- Monthly dues must be received by the 5th of each month.
- A grace period extends through the 7th.
- **Late Payment Fee**: A late fee of **Rs. 500** is assessed on the 8th for any unpaid dues.
- **Turnstile Deactivation**: Electronic card access is automatically paused if an account remains unpaid past the 10th of the month.
"""
    ),
    (
        "FEE-08_smoothie_bar_menu_and_allergens.md",
        """# FitZone Cafe: FuelBar Menu & Allergen Information
- **Document ID**: FEE-08
- **Category**: Cafe & Nutrition
- **Last Revised**: September 2026

## Popular Shakes & Prices
- **The Beast Builder (Rs. 650)**: 40g Whey Isolate, peanut butter, rolled oats, banana, whole milk.
- **Green Goddess Detox (Rs. 550)**: Spinach, cucumber, green apple, chia seeds, ginger, coconut water.
- **Berry Recovery Blast (Rs. 600)**: Mixed berries, glutamine, whey isolate, almond milk.
- **Keto Coffee Bomb (Rs. 450)**: Double espresso, MCT oil, grass-fed butter, collagen peptides.
- **Allergen Notice**: Blenders are sanitized between uses, but cross-contact with peanuts and tree nuts may occur. Dairy-free almond and oat milks available on request.
"""
    ),
    (
        "FEE-09_pro_shop_return_and_exchange_policy.md",
        """# FitZone Policy: Merchandise Return & Exchange Policy
- **Document ID**: FEE-09
- **Category**: Pro Shop & Retail
- **Last Revised**: September 2026

## Retail Return Guidelines
- **Apparel & Gear**: Items can be exchanged or returned for store credit within **14 calendar days** of purchase. Items must be unworn, unwashed, and have original retail tags attached.
- **Supplements**: Protein tubs and supplements can only be returned if the inner tamper-evident foil safety seal is completely intact.
- **Sale & Clearance Items**: Marked down final sale items cannot be returned.
"""
    ),
    (
        "FEE-10_corporate_billing_and_sponsorship.md",
        """# FitZone Policy: Corporate Group Retainer & Sponsorship
- **Document ID**: FEE-10
- **Category**: Corporate Accounts
- **Last Revised**: September 2026

## Corporate Retainer Terms
- Corporate wellness contracts require a minimum 6-month agreement.
- Companies are billed monthly on NET-30 terms via formal invoice.
- Employee roster updates must be submitted by the corporate HR representative by the 25th of each calendar month.
"""
    ),
]


def generate_all_documents() -> int:
    """Writes all 70 documents into the data/documents directory."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for filename, content in DOCUMENTS:
        filepath = DOCS_DIR / filename
        filepath.write_text(content.strip() + "\n", encoding="utf-8")
        count += 1
    print(f"Successfully generated {count} FitZone domain documents in: {DOCS_DIR}")
    return count


if __name__ == "__main__":
    generate_all_documents()

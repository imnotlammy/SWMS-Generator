from pathlib import Path
from datetime import date
import fitz

RISK_MATRIX = {
    5: {5:'E25',4:'E24',3:'E22',2:'E19',1:'H15'},
    4: {5:'E23',4:'E21',3:'E18',2:'H14',1:'H10'},
    3: {5:'E20',4:'H17',3:'H13',2:'M9',1:'M6'},
    2: {5:'H16',4:'H12',3:'M8',2:'L5',1:'L3'},
    1: {5:'M11',4:'M7',3:'L4',2:'L2',1:'L1'},
}

LIKELIHOODS = {1:'Rare',2:'Unlikely',3:'Possible',4:'Likely',5:'Almost certain'}
CONSEQUENCES = {1:'Insignificant',2:'Low',3:'Moderate',4:'High',5:'Catastrophic'}

# Presets are taken from the uploaded PR004 SWMS wording/controls.
HAZARD_PRESETS = {
    'Extreme weather': {
        'hazard':'Changing/exreme weather conditions cause work conditions to become unsafe',
        'controls':'Obtain and review weather report before accessing roof; continuously review conditions; record wind speed in Pre Start; cease work when conditions become unsafe.',
        'initial':(3,4),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'RF antennas': {
        'hazard':'Exposure to cooling towers and Radio Frequency antennas on the roof causes injury or harm',
        'controls':'Obtain current cooling tower inspection information; identify RF antenna locations; establish a safe work area.',
        'initial':(3,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Brittle or weak roof': {
        'hazard':'Working in or around brittle/weak roof structure causes technician to fall from height',
        'controls':'Identify and avoid weak/brittle roof areas; observe safety signs; cease work and contact manager if safety is uncertain.',
        'initial':(3,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Overhead power lines': {
        'hazard':'Ropes/equipment contact overhead power lines causing electrocution',
        'controls':'Maintain minimum 3 m separation from power lines; secure ropes away from lines; review exclusion zone/voltage and stop work if uncertain.',
        'initial':(3,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Moving vehicles/plant': {
        'hazard':'Ropes or equipment impact with moving vehicle/plant causing injury or death',
        'controls':'Keep technicians and equipment clear of vehicles/plant; establish exclusion zone where possible; secure ropes to prevent movement into traffic.',
        'initial':(3,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Restricted emergency access': {
        'hazard':'Restricted access/egress in an emergency delays rescue or medical care',
        'controls':'Provide two keys/swipes or ensure building manager/security can provide emergency access; establish direct communication; first aid kit onsite; minimum two technicians onsite.',
        'initial':(3,4),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Hazardous chemicals': {
        'hazard':'Incorrect use of hazardous chemical causes exposure and injury/harm',
        'controls':'Only trained technicians use hazardous chemicals; review SDS; provide necessary PPE; communicate chemical hazards before work.',
        'initial':(3,4),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Manual handling': {
        'hazard':'Incorrect manual handling while carrying/lifting equipment causes injury',
        'controls':'Use correct manual handling technique; use two people for heavy loads; split larger loads; make multiple trips with smaller loads.',
        'initial':(4,3),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Falling objects / exclusion zone': {
        'hazard':'Falling object or water strikes pedestrian, worker or property',
        'controls':'Establish dedicated exclusion zone with bollards and barricade tape/plastic chain; erect A-Frame danger sign; secure equipment with rated attachment points.',
        'initial':(4,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Animal habitat': {
        'hazard':'Contact with venomous animal causes injury or illness',
        'controls':'Inspect work areas for animal habitats; if nests/hives are identified, cease work, inform building manager and complete hazard report.',
        'initial':(2,4),'residual':(1,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Rescue access': {
        'hazard':'Difficult or restricted access in an emergency delays rescue and medical care',
        'controls':'Identify and discuss rescue system before descent; prepare contact rescue or pre-rigged rescue; keep first aid kit onsite.',
        'initial':(3,5),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
    'Public access': {
        'hazard':'Unauthorised public access to work/roof area causes incident or injury',
        'controls':'Where possible obtain keys so access doors can be locked while work is performed; maintain exclusion zones and site access controls.',
        'initial':(3,3),'residual':(2,2),'person':'Supervisor / All Technicians / Technician'
    },
}


def risk_code(likelihood: int, consequence: int) -> str:
    return RISK_MATRIX[int(consequence)][int(likelihood)]


def set_field(doc, name, value):
    for page in doc:
        for w in list(page.widgets() or []):
            if w.field_name == name:
                if w.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    w.field_value = 'Yes' if bool(value) else 'Off'
                else:
                    w.field_value = '' if value is None else str(value)
                w.update()
                return True
    return False


def set_combo(doc, name, value):
    for page in doc:
        for w in list(page.widgets() or []):
            if w.field_name == name:
                choices = getattr(w, 'choice_values', None) or []
                val = str(value)
                if choices and val not in choices:
                    # Preserve template spaces for blank options.
                    val = choices[-1] if not value else choices[0]
                w.field_value = val
                w.update()
                return True
    return False


def fill_worker(doc, index, worker):
    # First four workers live on page 15; remaining workers on page 16.
    if index < 4:
        n = index + 1
        set_field(doc, f'Workers nameRow{n}', worker.get('name',''))
        set_combo(doc, f'Dropdown5.{index}', worker.get('role',''))
        set_field(doc, f'Date9_af_date.{index}', worker.get('date',''))
        set_field(doc, f'Check Box{7+index}', worker.get('induction', False))
        set_field(doc, f'Check Box{11+index}', not worker.get('induction', False))
    else:
        n = index + 1
        set_field(doc, f'Workers nameRow{n}', worker.get('name',''))
        set_combo(doc, f'Dropdown6.{index-4}', worker.get('role',''))
        set_field(doc, f'Date10.{index-4}', worker.get('date',''))
        # Page 16 has 17 workers and 34 yes/no checkboxes in two blocks.
        row = index - 4
        if row < 9:
            set_field(doc, f'Check Box{15+row}', worker.get('induction', False))
            set_field(doc, f'Check Box{31+row}', not worker.get('induction', False))
        else:
            set_field(doc, f'Check Box{40+row-9}', worker.get('induction', False))
            set_field(doc, f'Check Box{49+row-9}', not worker.get('induction', False))


def generate_pdf(template_path, output_path, data):
    doc = fitz.open(template_path)

    # Page 1 metadata
    page1 = {
        'Client Name': data.get('client_name',''),
        'Contact Name': data.get('client_contact',''),
        'Address_2': data.get('client_address',''),
        'Mobile': data.get('mobile',''),
        'Work location': data.get('work_location',''),
        'Manager': data.get('manager',''),
        'Required Plant': data.get('required_plant',''),
        'Text1': data.get('jsea_preparer',''),
        'Date1_af_date': data.get('jsea_date_prepared',''),
        'Date2_af_date': data.get('jsea_provided',''),
    }
    for k,v in page1.items(): set_field(doc,k,v)
    set_field(doc,'Yes',data.get('site_specific',True))

    # Page 2 administration
    page2 = {
        'Text1': data.get('swms_preparer',''),
        'Start Time': data.get('start_time',''),
        'Date1_af_date': data.get('date_prepared',''),
        'Date2_af_date': data.get('last_review_date',''),
        'Date5_af_date': data.get('swms_provided',''),
        'Site Supervisor': data.get('site_supervisor',''),
        'First Aid officer': data.get('first_aid_officer',''),
        'Technician': data.get('lead_technician',''),
        'Total number of workers present on site': str(len([w for w in data.get('workers',[]) if w.get('name')])),
        'Copies of qualifications and certificates are available upon request please contact head office on 1300 301 214Row2': data.get('compliance_person',''),
    }
    for k,v in page2.items(): set_field(doc,k,v)
    set_combo(doc,'Dropdown1',data.get('supervisor_qualification','IRATA/SPRAT Lv 3'))
    set_combo(doc,'Dropdown2',data.get('technician_qualification','IRATA/SPRAT Technician'))
    set_field(doc,'Check Box5',True if data.get('site_supervisor_current',True) else False)
    set_field(doc,'11',True if data.get('first_aid_current',True) else False)
    set_field(doc,'Check',True if data.get('technician_current',True) else False)

    # PPE checkboxes in the template, in the displayed order.
    ppe_fields = [f'Yes_{i}' for i in range(2,19)]
    for f in ppe_fields: set_field(doc,f,True)

    # Pre-start requirements selected by user.
    for field, key in [('Check Box2','site_induction'),('1','general_induction'),('2','access_permit'),('3','roof_access_permit'),('4','working_at_heights_permit')]:
        set_field(doc,field,data.get(key,False))

    # Page 14 site-specific hazard/task rows.
    for idx,row in enumerate(data.get('site_specific_rows',[])[:5], start=1):
        fields = {
            f'Break job down into discrete steps Each step should accomplish some major task and be in a logical sequenceRow{idx}': row.get('number',str(idx)),
            f'Break job down into discrete steps Each step should accomplish some major task and be in a logical sequenceRow{idx}_2': row.get('activity',''),
            f'Identify the hazards associated with each step and examine each to identify possibilities that could lead to an accidentRow{idx}': row.get('hazard',''),
            f'Refer to the Risk MatrixRow{idx}': row.get('risk',''),
            f'Consider number of people required to carry out a task training skills and competencies required licences permits etc environmental controls plant tools and equipment safety equipment and PPE etcRow{idx}': row.get('controls',''),
            f'Refer to Risk MatrixRow{idx}': row.get('residual',''),
            f'List persons responsible for thisRow{idx}': row.get('person',''),
        }
        for k,v in fields.items(): set_field(doc,k,v)

    # Worker amendment section on page 14.
    roles = [('Site Supervisor','NameSite Supervisor'),('First Aid officer','NameFirst Aid officer'),('Technician','NameTechnician'),('Technician','NameTechnician_2')]
    for i,(role,field) in enumerate(roles):
        worker = data.get('role_workers',[])[i] if i < len(data.get('role_workers',[])) else {}
        set_field(doc,field,worker.get('name',''))
        set_combo(doc,f'Dropdown4.{i}' if i>1 else ('Dropdown3' if i==0 else 'Dropdown4.0'), worker.get('qualification',' ' if i==0 else 'IRATA/SPRAT Technician'))
        yes_field = ['Check Box6','Check Box21','Check Box22','Check Box23'][i]
        no_field = ['Check Box24','Check Box25','Check Box26','Check Box27'][i]
        set_field(doc,yes_field,worker.get('current',False))
        set_field(doc,no_field,not worker.get('current',False))

    # Employee acknowledgement rows.
    for i,w in enumerate([x for x in data.get('workers',[]) if x.get('name')][:21]):
        fill_worker(doc,i,w)

    set_field(doc,'Date6_af_date',data.get('facilities_manager_date',''))
    set_field(doc,'Date7_af_date',data.get('facilities_manager_signature_date',''))
    set_field(doc,'Date8_af_date',data.get('review_date',''))

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path

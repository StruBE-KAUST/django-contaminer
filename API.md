# API documentation

This django application provides an API to interact with ContaMiner. This API
gives a way to consult the ContaBase (contaminants database), submit a new
job, and retrieve the state and the result of a given job. However, this API
does not allow to update the ContaBase or a previous job, neither to cancel
or remove a job or a contaminant.

This documentation is divided in three sections.

1. [Common workflow](#common-workflow)
2. [General structure of the data](#general-structure)
3. [Functions documentation](#functions-documentation)

All the requests are made over HTTP(S). Depending on the function called, you
could have to use either GET or POST.

## Common workflow
The most probable workflow would be to get the list of contaminants,
display a form to the end-user allowing him to upload a file, select some
contaminants, and submit the form.
When receiving the data from the end-user, the data can be sent to this django
application through the API. A job ID is sent in response.
This job ID can be used to follow the status of the job.
When the status is "complete", the details of the results can be retrieved, 
and displayed to the end-user.
```
 __________         ____________        ____________________
|          |       |            |      |                    |
| End-user |       | Web server |      | Django application |
|__________|       |____________|      |  (API provider)    |
     |                   |             |____________________|
     |                   |                       |
     |                   |   GET contaminants    |
     |                   |---------------------->|
     |                   |                       |
     |                   |  contaminants (JSON)  |
     |                   |<----------------------|
     |                   |                       |
     |    Display form   |                       |
     |<------------------|                       |
     |                   |                       |
     |     Send form     |                       |
     |------------------>|                       |
     |                   |__                     |
     |                   |  |                    |
     |                   |  | Local stuff        |
     |                   |  |                    |
     |                   |<--                    |
     |                   |                       |
     |                   |    POST submit_job    |
     |                   |---------------------->|
     |                   |                       |
     |                   |     job ID (JSON)     |
     |                   |<----------------------|
     |                   |                       |
     |                   |                       |<--
     |                   |       GET status      |   |
     |                   |---------------------->|   |
     |                   |                       |  Repeat until
     |                   |     status (JSON)     |  status is
     |                   |<----------------------|  "Complete"
     |                   |                       |   |
     |                   |                       |___|
     |                   |                       |
     |                   |      GET results      |
     |                   |---------------------->|
     |                   |                       |
     |                   |       results (JSON)  |
     |                   |<----------------------|
     |                   |                       |
     |  Display results  |                       |
     |<------------------|                       |
     |                   |                       |
```

This workflow can be modified, for example by using a cache version of the 
list of contaminants. 

A more advanced workflow can take advantage of the various available of
a job. 
```
 __________         ____________        ____________________
|          |       |            |      |                    |
| End-user |       | Web server |      | Django application |
|__________|       |____________|      |  (API provider)    |
     |                   |             |____________________|
     |                   |                       |
     |                   |   GET contaminants    |
     |                   |---------------------->|
     |                   |                       |
     |                   |  contaminants (JSON)  |
     |                   |<----------------------|
     |                   |                       |
     |    Display form   |                       |
     |<------------------|                       |
     |                   |                       |
     |     Send form     |                       |
     |------------------>|                       |
     |                   |__                     |
     |                   |  |                    |
     |                   |  | Local stuff        |
     |                   |  |                    |
     |                   |<--                    |
     |                   |                       |
     |                   |    POST submit_job    |
     |                   |---------------------->|
     |                   |                       |
     |                   |     job ID (JSON)     |
     |                   |<----------------------|
     |                   |                       |
     |   Loading page    |                       |
     |<------------------|                       |
     |                   |                       |<--
     |                   |       GET status      |   |
     |                   |---------------------->|   |
     |                   |                       |  Repeat until
     |                   |     status (JSON)     |  status is
     |                   |<----------------------|  "Running"
     |                   |                       |   |
     |                   |                       |___|
     |                   |                       |
     |                   |                       |
     |                   |                       |<--
     |                   |      GET results      |   |
     |                   |---------------------->|   |
     |                   |                       |   |
     |                   |       results (JSON)  |  Repeat until
     |                   |<----------------------|  status is
     |                   |                       |  "Complete"
     |  Display results  |                       |   |
     |<------------------|                       |   |
     |                   |                       |___|
     |                   |                       |
```
Such a workflow allows the Web server to display live results to the End-user,
while waiting less time before getting the first results.

## General structure
Data sent as a reply to a query follow a given structure. This structure is
shown in this section.

#### Convention used
Words starting with an uppercase are objects. Words starting with a lowercase
are primary elements (int, string, ...)

A link = is unique (One to One) and gives a 'key': 'value' relationship in
JSON.

A link * is multiple (One to Many) and gives a 'key': ['value1', 'value2',...]
in JSON.

#### ContaBase
The first block shows the structure of the ContaBase, as given when querying
the full list of contaminants. This structure is used only to give some
information about ContaBase (as opposed to ContaMiner which manages jobs).
```
ContaBase       Database of possible contaminants which may cristallise
  |             instead of a protein of interest. The contabase also contains
  |             the models prepared by morda_prep for a molecular replacement
  |
  |*Category      General classification of the contaminants
    |             Based on the origin of the contaminants.
    |             Allows the user to know if he should test this contaminant
    |
    |=id         (int) Unique identifier of the category
    |
    |=name       (string) Common designation of the category
    |
    |=default    (bool) Contaminants in this category are tested by
    |             default if $default is true. Contaminants in this
    |             category are ignored by default if $default is false. A
    |             specific user input overwrite this default behavior.
    |
    |*Contaminant   Protein which may cristallise instead of a protein of
      |             interest.
      |
      |=uniprot_id (string) Unique identifier used on Uniprot
      |             to label the protein
      |
      |=short_name (string) Common short name of the protein
      |
      |=long_name  (string)(opt) Common name of the protein
      |
      |=sequence   (string) Amino-acid sequence of the protein
      |
      |=organism   (string)(opt) Origin of the contaminant
      |
      |
      |*Pack          Set of models prepared by morda_prep, and used by
      | |             morda_solve. A pack is included in a unit cell during
      | |             the molecular replacement process.
      | |
      | |=number      (int) Number of the pack. This number is unique among
      | |             other packs for the same contaminant, but not unique
      | |             in the ContaBase.
      | |
      | |=structure   (string) Quaternary structure. Can be :
      | |             * "1-mer" for a monomer
      | |             * "domains" for a set of domains
      | |             * "2-mer", "3-mer", "4-mer", ...  for a multimer
      | |
      | *Model          Specific chain and domain of a template
      |   |
      |   |=template   (string) PDB ID of the template used to create the
      |   |             model
      |   |
      |   |=chain      (string)(opt) Chain of the template used to create the
      |   |             model
      |   |
      |   |=domain     (string)(opt) Domain of the template used to create
      |   |             the model
      |   |
      |   |=residues   (int) Number of residues in the model
      |
      |
      |*Reference     Reference to a publication mentioning the protein as a 
      | |             contaminant
      | |
      | |=pubmed_id   (int) Unique identifier of the publication on PubMed
      |
      |*Suggestion    Suggestion to add this protein as a contaminant from a
        |             personnal communication
        |
        |=name        (string) Firstname Lastname of the person who suggested
                      the protein as a contaminant
```

#### ContaMiner
The second block shows the structure of the jobs, as managed by ContaMiner.
This structure is used only to manage jobs (submit, get the status, and 
retrieve the results).
```
Job             Set of tasks to run with one unique diffraction data file.
  |             One job allows the user to know if any contaminant is in his
  |             crystal.
  |
  |=id            (int) Unique identifier of the job
  |
  |=status        (string) Current status of the job. Can be:
  |               * "New" if the job has been created but not submitted to the
  |               cluster.
  |               * "Submitted" when the file is uploaded to the cluster, and
  |               the tasks are queued
  |               * "Running" if the tasks are running on the cluster
  |               * "Complete" when all the tasks for this job are complete
  |               * "Error" if an error has been encountered (bad file,
  |               bad list of contaminants, cluster down, ...)
  |
  |=name          (string) Name of the job, as given during the submission.
  |
  |*Task          Result of morda_solve for one combinaison of contaminant,
    |             pack and space group.
    |             The set (uniprot_id, pack_nb, space_group) is unique among
    |             the results for one single job.
    |
    |=uniprot_id    (string) Uniprot ID of the contaminant tested
    |
    |=pack_nb       (int) Number of the pack tested. See the number attribute
    |               of the Pack object in the ContaBase.
    |
    |=space_group   (string) Space group in which the pack is tested.
    |               Indexes are seperated by dashes. Ex:
    |               P-21-21-21
    |
    |=status        (string) Status of the task. Can be:
    |               * "New" if the task did not yet start
    |               * "Running" if the task is running on the cluster
    |               * "Complete"
    |               * "Error" if an error has been encountered
    |
    |=percent       (int) probability for solution to be a good solution.
    |               See MoRDa documentation for more details
    |
    |=q_factor      (float)Indicator of the solution quality.
    |               See MoRDa documentation for more details
```

## Functions documentation
This section provides the needed information to interact with ContaMiner
through the API. Each function description goes with one or more examples
requests and responses.

In the Example Requests, `{domain}` represents the root URL to your ContaMiner
django installation. To access the service hosted in KAUST, replace `{domain}`
by 
[`https://strube.cbrc.kaust.edu.sa/contaminer`](https://strube.cbrc.kaust.edu.sa/contaminer).


Here is the list of available functions.
 * [GET contabase](#get-contabase)
 * [GET categories](#get-categories)
 * [GET detailed_categories](#get-detailed_categories)
 * [GET category](#get-category)
 * [GET detailed_category](#get-detailed_category)
 * [GET contaminants](#get-contaminants)
 * [GET detailed_contaminants](#get-detailed_contaminants)
 * [GET contaminant](#get-contaminant)
 * [GET detailed_contaminant](#get-detailed_contaminant)
 * [POST job](#post-job)
 * [GET job/status](#get-jobstatus)
 * [GET job/result](#get-jobresult)
 * [GET job/detailed_result](#get-jobdetailed_result)
 * [GET job/final_pdb](#get-jobfinal_pdb)
 * [GET job/final_mtz](#get-jobfinal_mtz)

#### GET contabase

> Parameters: none
>
>
> Return the complete ContaBase

###### Example Request
```
GET https://{domain}/api/contabase
```

###### Example Response
```
{
    "categories": [
        {
            "id": 1,
            "name": "Protein in E.Coli",
            "selected_by_default": true,
            "contaminants": [
                {
                    "uniprot_id": "P0ACJ8",
                    "short_name": "CRP_ECOLI",
                    "long_name": "cAMP-activated global transcriptional regulator CRP",
                    "sequence": "MVLGKPQTDPTLEW[...Truncated output ...]ISAHGKTIVVYGTR",
                    "organism": "E. Coli",
                    "packs": [
                        {
                            "number": 1,
                            "structure": "1-mer",
                            "models": [
                                {
                                    "template": "3RYP",
                                    "chain": "A",
                                    "domain": 0,
                                    "identity": 1.000,
                                    "residues": 202
                                }
                            ]
                        },
                        {
                            "number": 2,
                            "structure": "domains",
                            "models": [
                                {
                                    "template": "3RYP",
                                    "chain": "A",
                                    "domain": 1,
                                    "identity": 1.000,
                                    "residues": 112
                                },
                                {
                                    "template": "3RYP",
                                    "chain": "A",
                                    "domain": 2,
                                    "identity": 1.000,
                                    "residues": 71
                                }
                            ]
                        },
                        [... Truncated output ...]
                    ],
                    "references": [
                        {
                            "pubmed_id": 26660914
                        },
                        {
                            "pubmed_id": 16814929
                        }
                    ]
                },
                [... Truncated output ...]
            ]
        },
        {
            "id": 2,
            "name": "Tag",
            "selected_by_default": false,
            "contaminants": [
                [... Truncated output ...]
                ]
        }
        [... Truncated output ...]
    ]
}
```

#### GET categories

> Parameters: none
>
>
> Return the list of categories

###### Example Request
```
GET https://{domain}/api/categories
```

###### Example Response
```
{
    "categories": [
        {
            "id": 1,
            "name": "Protein in E.Coli",
            "selected_by_default": true
        },
        {
            "id": 2,
            "name": "Tag",
            "selected_by_default": false
        },
        {
            "id": 3,
            "name": "Protein used during purification or crystallisation",
            "selected_by_default": false
        },
        {
            "id": 4,
            "name": "Protein in yeast",
            "selected_by_default": false
        },
        {
            "id": 5,
            "name": "Microbial contaminants of host cell and reagents",
            "selected_by_default": true
        },
        {
            "id": 6
            "name": "Other expression systems",
            "selected_by_default": true
        }
     ]
}
```

#### GET detailed_categories
> Parameters: none
>
>
> Return the list of categories, with the included contaminants

The response is exactly the same as GET contabase.

###### Example Request
```
GET https://{domain}/api/detailed_categories
```

###### Example Response
See GET contabase

#### GET category
> Parameters:
> * (int) category_id
>
>
> Return the category with the given ID

###### Example Request
```
GET https://{domain}/api/category/2
```

###### Example Response
```
{
    "category": {
        "id": 2,
        "name": "Tag",
        "selected_by_default": false
    }
}
```

#### GET detailed_category
> Parameters:
> * (int) category ID
>
>
> Return the category with the given ID, with the included contaminants

###### Example Request
```
GET https://{domain}/api/detaild_category/2
```

###### Example Response
```
{
    "id": 2,
    "name": "Tag",
    "selected_by_default": false,
    "contaminants": [
        {
            "uniprot_id": "P0AA25",
            "short_name": "THIO_ECOLI",
            "long_name": "Thioredoxin-1",
            "sequence": "MSDKIIHLTDDSF[... Truncated output ...]SKGQLKEFLDANLA",
            "organism": "E. Coli",
            "packs": [
                {
                    "number": 1,
                    "structure": "1-mer",
                    "models": [
                        {
                            "template": "3DXB",
                            "chain": "B",
                            "domain": 0,
                            "identity": 1.000,
                            "residues": 107
                        }
                    ]
                },
                {
                    "number": 2,
                    "structure": "4-mer",
                    "models": [
                        {
                            "template": "3DXB",
                            "chain": "ABCD",
                            "domain": 0,
                            "identity": 1.000,
                            "residues": 107
                        }
                    ]
                },
                [... Truncated output ...]
            ],
            "references": [
                {
                    "pubmed_id": 26660914
                }
            ]
        },
        {
            "uniprot_id": "P63165",
            "short_name": "SUMO1_HUMAN",
            "long_name": "Small ubiquitin-related modifier 1",
            [... Truncated output ...]
        },
        [... Truncated output ...]
    ]
}
```

#### GET contaminants
> Parameters: none
>
>
> Return the list of contaminants without the categories

###### Example Request
```
GET https://{domain}/api/contaminants
```

###### Example Response
```
{
    "contaminants": [
        {
            "uniprot_id": "P0ACJ8",
            "short_name": "CRP_ECOLI",
            "long_name": "cAMP-activated global transcriptional regulator CRP",
            "sequence": "MVLGKPQTDPTLE[... Truncated output ...]ISAHGKTIVVYGTR",
            "organism": "E.Coli"
        },
        {
            "uniprot_id": "P0AA25",
            "short_name": "THIO_ECOLI",
            "long_name": "Thioredoxin-1",
            "sequence": "MSDKIIHLTDDSF[... Truncated output ...]SKGQLKEFLDANLA",
            "organism": "E. Coli"
        },
        {
            "uniprot_id": "P63165",
            "short_name": "SUMO1_HUMAN",
            "long_name": "Small ubiquitin-related modifier 1",
            "sequence": "MSDQEAKPSTEDL[... Truncated output ...]IEVYQEQTGGHSTV",
            "organism": "Homo sapiens"
        },
        [... Truncated output ...]
    ]
}
```

#### GET detailed_contaminants
> Parameters: none
>
>
> Return the list of contaminants without the categories, with the packs

###### Example Request
```
GET https://{domain}/api/detailed_contaminants
```

###### Example Response
```
{
    "contaminants": [
        { 
            "uniprot_id": "P0AA25",
            "short_name": "THIO_ECOLI",
            "long_name": "Thioredoxin-1",
            "sequence": "MSDKIIHLTDDSF[... Truncated output ...]SKGQLKEFLDANLA",
            "organism": "E.Coli",
            "packs": [
                {
                    "number": 1,
                    "structure": "1-mer",
                    "models": [
                        {
                            "template": "3DXB",
                            "chain": "B",
                            "domain": 0,
                            "identity": 1.000,
                            "residues": 107
                        }
                    ]
                },
                {
                    "number": 1,
                    "structure": "4-mer",
                    "models": [
                        {
                            "template": "3DXB",
                            "chain": "ABCD",
                            "domain": 0,
                            "identity": 1.000,
                            "residues": 107
                        }
                    ]
                },
                [... Truncated output ...]
            ],
            "references": [
                {
                    "pubmed_id": 26660914
                }
            ]
        },
        {
            "uniprot_id": "P63165",
            "short_name": "SUMO1_HUMAN",
            "long_name": "Small ubiquitin-related modifier 1",
            [... Truncated output ...]
        },
        [... Truncated output ...]
    ]
}
```

#### GET contaminant
> Parameters:
> * (string) uniprot ID
>
>
> Return the contaminant with the given uniprot ID

###### Example Request
```
GET https://{domain}/api/contaminant/P0AA25
```

###### Example Response
```
{
    "uniprot_id": "P0AA25",
    "short_name": "THIO_ECOLI",
    "long_name": "Thioredoxin-1",
    "sequence": "MSDKIIHLTDDSF[... Truncated output ...]SKGQLKEFLDANLA",
    "organism": "E. Coli",
}
```

#### GET detailed_contaminant
> Parameters:
> * (string) uniprot ID
>
>
> Return the contaminant with the given uniprot ID, with the packs and
references

###### Example Request
```
GET https://{domain}/contaminer/api/contaminant/P0AA25
```

###### Example Response
```
{
    "uniprot_id": "P0AA25",
    "short_name": "THIO_ECOLI",
    "long_name": "Thioredoxin-1",
    "sequence": "MSDKIIHLTDDSF[... Truncated output ...]SKGQLKEFLDANLA",
    "organism": "E. Coli",
    "packs": [
        {
            "number": 1,
            "structure": "1-mer",
            "models": [
                {
                    "template": "3DXB",
                    "chain": "B",
                    "domain": 0,
                    "identity": 1.000,
                    "residues": 107
                }
            ]
        },
        {
            "number": 1,
            "structure": "4-mer",
            "models": [
                {
                    "template": "3DXB",
                    "chain": "ABCD",
                    "domain": 0,
                    "identity": 1.000,
                    "residues": 107
                }
            ]
        },
        [... Truncated output ...]
    ],
    "references": [
        {
            "pubmed_id": 26660914
        }
    ]
}
```

#### POST job
> Parameters:
> * (file) diffraction_data
> * (string)(opt) contaminants
> * (files)(opt) custom_models
> * (string)(opt) email_address
> * (string)(opt) name
>
>
> Return a new job ID and submits the job to the cluster
>
>
> Return an error if the submitted file is not valid


This function submits a new job to the cluster. The job uses
the diffraction data from `diffraction_data`, and tests
it against the contaminants whose uniprot IDs are in
`contaminants`, and/or against the models in `custom_models`.
Either `contaminants` or `custom_models` has to be provided (or both).
If available, `email_address` is used to send a
notification email when the job is submitted, then complete.

`contaminants` is a list of the uniprot IDs, separated by
commas, without space.


###### Example Request
```
POST https://{domain}/api/job
```
with:
```
$_POST['email_address'] = 'you@example.com'
$_POST['name'] = 'Is that MBP?'
$_POST['contaminants'] = "P0ACJ8,P0AA25,P63165"
$_FILES['diffraction_data'] = A valid diffraction file
```

###### Example Response
```
{
    "error": false,
    "id": 168,
}
```

###### Example Request
```
POST https://{domain}/api/job
```
with:
```
$_POST['email_address'] = 'you@example.com'
$_POST['contaminants'] = "P0ACJ8,P0AA25,P63165"
$_FILES['diffraction_data'] = An invalid diffraction file
```

###### Example Response
```
{
    "error": true,
    "message": "Invalid data file"
}
```

###### Example Request
```
POST http://{domain}/api/job
```
with:
```
$_POST['email_address'] = 'you@example.com'
$_POST['name'] = 'MBP or my contaminant?'
$_POST['contaminants'] = "P0ACJ8,P0AA25,P63165"
$_FILES['diffraction_data'] = A valid diffraction file
$_FILES['custom_models'] = A list of valid PDB files
```

###### Example Response
```
{
    "error": false,
    "id": 169,
}
```

#### GET job/status
> Parameters:
> * (int) job ID
>
>
> Return the current status of the job with the given job ID.
> The returned status can be:
> * "New": when the file has been submitted to the web server,
but the job is not submitted to the cluster. (Live results are
not available)
> * "Submitted": when the file is uploaded to the server and
the tasks are queued. (Live results are not available)
> * "Running": when the tasks started on the cluster. (Live
results are available)
> * "Complete": when all the tasks are complete on the cluster.
> * "Error": when an error has been encountered.

###### Example Request
```
GET https://{domain}/api/job/status/165
```

###### Example Response
```
{
    "id": 165,
    "status": "Submitted"
}
```

#### GET job/result
> Parameters:
> * (int) job ID
>
>
> Return the resuls for the job with the given ID if the job is "Running", or
"Complete"
>
>
> Return an error if the job does not exist or its status is "Error"
> Returns empty results if the job if "New" or "Submitted"


Use [`GET job/status`](#get-jobstatus) to know the current state of the job.


The `pack_number` and `space_group` are the combinaison giving the best
`q_factor` and `percent` for this `job` and `contaminant`. `files_available`
indicates if the final files are available for download through the adequate
URL (see [`GET job/final_pdb`](#get-jobfinal_pdb) and [`GET job/final_mtz`](#get-jobfinal_mtz)).

The `uniprot_id` for a user-provided model is `c_` followed by the filename of
the submitted file (without the extension).

A `messages['bad_model']` field is returned in the response if a positive result is found
for a contaminant without a known model in the Protein Data Bank.

###### Example Request
```
GET https://{domain}/api/result/166
```

###### Example Response
```
{
    "error": true,
    "message": "Job does not exist"
}
```

###### Example Request
```
GET https://{domain}/api/job/result/165
```

###### Example Response
```
{
    "id": 169,
    "results": [
        {
            "uniprot_id": "P0ACJ8",
            "status": "Complete",
            "percent": 51,
            "q_factor": 0.469,
            "pack_number": 1,
            "space_group": "P-1-2-1",
            "files_available": "False"
        },
        {
            "uniprot_id": "P0AA25",
            "status": "Complete",
            "percent": 99,
            "q_factor": 0.871
            "pack_number": 3,
            "space_group": "P-1-2-1",
            "files_available": "True"
        },
        {
            "uniprot_id": "P63165",
            "status": "Running",
            "percent": 0,
            "q_factor": 0,
            "files_available": "False"
        }
        {
            "uniprot_id": "c_myfile",
            "status": "Running",
            "percent": 0,
            "q_factor": 0,
            "files_available": "False"
        }
    ],
    "messages": {
        "bad_model": "Your dataset gives a positive result for [... Truncated output ...]"
    }
}
```

#### GET job/detailed_result
> Parameters:
> * (int) job ID
>
>
> Return the results for the job with the given ID,
> with the result for each space group and pack pairs if the job is "Running", 
or "Complete".
>
>
> Return an error if the job does not exist or its status is "Error"
>
>
> Return empty results if the job is "New" or "Submitted"

Use [`GET job/status`](#get-jobstatus) to know the current state of the job. `files_available`
indicates if the final files are available for download through the adequate
URL (see [`GET job/final_pdb`](#get-jobfinal_pdb) and [`GET job/final_mtz`](#get-jobfinal_mzt))

The `uniprot_id` for a user-provided model is `c_` followed by the filename of
the submitted file (without the extension).

###### Example Request
```
GET https://{domain}/api/job/detailed_result/166
```

###### Example Response
```
{
    "error": true,
    "message": "Job does not exist"
}
```

### Example Request
> GET https://{domain}/api/job/detailed_result/164

### Example Response
```
{
    "id": 164,
    "results": [
        {
             "contaminant_id": "P0ACJ8",
             "pack_nb": 1,
             "space_group": "P-1-2-1",
             "status": "Complete",
             "percent": 40,
             "q_factor": 0.411,
             "files_available": "False"
        },
        {
            "contaminant_id": "P0ACJ8",
            "pack_nb": 2,
            "space_group": "P-1-2-1",
            "status": "Complete",
            "percent": 51,
            "q_factor": 0.469,
            "files_available": "False"
        },
        [... Truncated output ...]
        {
            "contaminant_id": "P0AA25",
            "pack_nb": 1,
            "space_group": "P-1-2-1",
            "status": "Complete",
            "percent": 99,
            "q_factor": 0.871,
            "files_available": "True"
        },
        [... Truncated output ...]
    ] 
}
```

#### GET job/final_pdb
> Parameters:
> * (int) id
> * (string) uniprot_id
> * (string) space_group
> * (int) pack_nb
>
>
> Return the final PDB file generated by `morda_solve` for the
> job with the given ID, tested against the contaminant
> with the given uniprot ID, in the given space group
> (for example P-21-21-21), and the given pack number.

The file is available only if the result for the combination
of contaminant, space group and pack gave a result with
a percentage higher than 90. The file is kept for a limited time on
the server. Check the `files_available` field of
[`GET job/result`](#get-result) and [`GET job/detailed_result`](#get-detailed_result)

> Return an error if the file is not available.

###### Example Request
```
GET https://{domain}/api/job/final_pdb?id=165&uniprot_id=P0ACJ8&space_group=P-1-2-1&pack_nb=1
```

###### Example Response
```
{
    "error": true",
    "message": "File does not exist"
}
```

###### Example Request
```
GET https://{domain}/api/job/final_pdb?id=165&uniprot_id=P00025&space_group=P-1-2-1&pack_nb=1
```

###### Example Response
PDB file content

#### GET job/final_mtz
> Parameters:
> * (int) id
> * (string) uniprot_id
> * (string) space_group
> * (int) pack_nb
>
>
> Return the final MTZ file generated by `morda_solve` for the
> job with the given ID, tested against the contaminant
> with the given uniprot ID, in the given space group
> (for example P-21-21-21), and the given pack number.

The file is available only if the result for the combination
of contaminant, space group and pack gave a result with
a percentage higher than 90. The file is kept for a limited time on
the server. Check the `files_available` field of
[`GET job/result`](#get-result) and [`GET job/detailed_result`](#get-detailed_result)

> Return an error if the file is not available

###### Example Request
```
GET https://{domain}/api/job/final_mtz?id=165&uniprot_id=P0ACJ8&space_group=P-1-2-1&pack_nb=1
```

###### Example Response
```
{
    "error": true",
    "message": "File does not exist"
}
```

###### Example Request
```
GET https://{domain}/api/job/final_mtz?id=165&uniprot_id=P00025&space_group=P-1-2-1&pack_nb=1
```

###### Example Response
MTZ file content

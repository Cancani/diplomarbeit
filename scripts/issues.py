#!/usr/bin/env python3
"""Preview/create/update issues from backlog.json; never silently discard edits."""
import argparse
import hashlib
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- diplomarbeit:backlog:start -->'
END = '<!-- diplomarbeit:backlog:end -->'
HISTORY = '## Früher abgehakte Kriterien (historisch)'
TEMPLATE_HASHES = {
    'US01': ('4bd2dd50c199a9a99125762d3aa5a3a012ada09ef204f486f019c3e0a6806dfc', '9e43e524af5fd6a9cb0c68319467c63cd522af3aee36fc08f1f4e41ba86598b5', 'c51e57130bc434b1fcb6d5b7c98e0affbaf4bd9c6186f4c030d7c62e26be0014'),
    'US02': ('b87c92d2c09f09b9c0905a100dc3195755f2a6af2fedb72d46542859791e32b1', 'e7ffc7cc60519b074128ce626af3faa0f93db9984dcc1647995351e01935fc9c', 'f3088fa940ff615fe5f2ef7d58ff62d394a7f551cb538886c91c4efd22a97d95'),
    'US03': ('5cefa22372c32cc4742f4902dd8449d3c0a481e064deb451a526c3394c2f802a', 'b521b969e2d13ba4883b590a70e259dd83e6d407260d691718e31cda49951d4c', 'd443998270dd2a9a2ee465cff0e4c97352a0b29d93857cc0c1f15a8d447467c4'),
    'US04': ('907d64bc44c8d025e80445124afa7c4a586ed20be9844b417a39ca926229cf55', '99b05f1525e6653dcf807d564514fd5e324be47aca2c75362498ec393e7525f0', 'e8ace7fa834b2c3cccf36eec3313a50473f7b1bca72ce373826ffcd02e6f5b1c'),
    'US05': ('225552416c32c3cbbe39cd57f605c3d28a991af02929321d80e64131cba2ac9b', '316e9f7152b9e3987bc5bd515ebcf1067de3869d38ffc791f6ab8e668a8e975f', 'f2fbcd15cbc9ce8e3afeb3816ba8560f2dc233aa387dabecef6d228f24013b51'),
    'US06': ('333fac31154f7c55c980b93666f1bbfec8471cbaaefc64e7a7c5ee46a897cec5', '5cfd019cdce515c696bf774318e9b50b51ddb09686f37a640e95fd3fb0dafe47', 'e730e112a242f61ccf364cb0b0e3b7fdb06ecb447782ee623c33536db7d78f41'),
    'US07': ('480b715329d727b0aeb95c4958df5d6730a1ff772d009994aaf0af6680b7b1c1', 'def702e30493b2aeb0d52ce175a8afbce04dd927cd05cf12fa4ae14212f4460a', 'ec1d30097ef8735644e00cdb0228c1a3cf47300bd3905e2456e9a3d72660bbbd'),
    'US08': ('0a917fdb8e04a9f1c5f47085f9ffb134a84247313bea035425c8e94be3521ed1', '98f4db011941b407388855f5bbca6c41c11ff11b51406923f5c653b3b1af35b2', 'd8667c1ebfc69d15dd5b58c25f4868f426ba8b52d3fda7f9a605e6469dd8ce79'),
    'US09': ('16fe5776e04300932de168306919dd80662a8af5206254bc44263b8421f7ee2d', '525a2134a7da8e238c17b473d1b0348d92445c4fb4e253ceb7808e463ab63c34', '6f1d0e26e3bc9e2e1ebb06eccc725de25aed2f71e96dd06f97241a905b0227e0'),
    'US10': ('0a83448ddccff40a443b2699aa5573a4e75785798041ba1bb35f948cd6cde916', '91c8ec28b4361ecc1fa2d993a326dbd4f34aa6725a7c8f606b70769c3a9a17fd', 'c2a6ebd6b277179776fcadd5d3a21bdca45dd7a3d3d595ca8a19ba6fe0825782'),
    'US11': ('36ea53cd7efb0f4a6f8c0a36dfc23a0041520d4eb1638e507c60685d2281c87f', 'a622881a9f527d0baa6b897178b7f227cc6dbdb59b96ad81679a8e3c214f21ba', 'a7ad55fef0e901550d1953339fd33b00cf5ad13148c3b22c1b09a610063246f2'),
    'US12': ('4c82d921efbbdc2255ba40e134f670274b1b00965e7901975dd3b5c28dd5168f', '8d80122677bf0beac4f096f0a7cf41d5800af3ee6bd8215a1b0138d4c6688648', '9ffe8f5ea8f00ae89d567a9b5d19b08ad8796e02c08d445fdde7d3480f1a7a82'),
    'US13': ('5ab780c82803f2da9676d2219418e2dc994428904d522c3ccdfa95badbf07f01', 'ddc7478f5b246977662e4e5a42ff90e0cd3eb51e6bc13f67b8912fdeb0aaba57', 'df1b094b3c97ee8a05ca929824cf6ea1c51dcf0958027f7282cac194a0e95b05'),
    'US14': ('62c6abda4e43244a5393fde767d2df0273df01c19ecc112a0e148d5e8fec1870', 'b17ae5be5c57da1aa3f51fb5993a210bda1d0fadbdccf7738f009d994f04357d', 'cc8bdbef05072f3ea370884236e68e55cf729ee7c5e4eeeb127b7730f75ac6a0'),
    'US15': ('536a9937487e94b75b0c3b9bf942ac53ee9e132187721b9bf379f4202a1a3cff', '8442ea7ebcdbf2a40f128bc2c1c6b9d6b37df73e80564c6b7c13f9521dd6f0d7', 'd9db8f7d4c648cc02608f27fd0d93e2a4c50fa52c47c4a2d5caa3db4dbf835ca'),
    'US16': ('a26beb21629d46bcc4b6360306c7aeaaabb5678414cc6bb5617ab17dbd36c4a2', 'f751ca33f6428bd26f0abb72ca05475c3d9c2e2b5013d18279be8e5b2296e547', 'f87fb1a61d211c01def7e6793ba15a509eff59f55eeefecd99e4cb5099fa4339'),
    'US17': ('1f011c52b5f975b2e4e73d7ed02ab3299807b5297ca080f1b9dce87e5eb71497', '451acf5afe6c77f573cdef04111cd6f15fce44e836bc59baac2117e79db07be7', 'a14dd6875c7ee82437866e3cdbba1891cef682b12de76a01f20f04a03e95eb89'),
    'US18': ('15372ca59ab911e950c4c9096dfc2d1af0fe6a59270b32f739db53905f6ecddd', '45a1435c987862cefaa5999e8489ecd1f07314dc7fa7c317ed57bb621fdf4a9b', '7206d114345de44d186c4a19c7e129c193f4b4983954f298253960ea8194c914'),
    'US19': ('26970ea8a4e1cb61566f5892edea5fe9c75494cc59af6d8888920f7d06d8f650', '26adc40f5eea6bf19b7639c0ce8b73861519df85964d8278aab363ad1f8dd344', '5c8159584805e94d771d5fbd102175402a1ca832a106921f626b3cdf0bee3b94'),
    'US20': ('e1e8256a2473b79ab65c67082cd1e6e15590203955c19a98d89e8f42e727a92c', 'f22e25ece864aaad85ff549864cfa7d71e00938dc8eba8155a4c3ed03e4bc260', 'fc732e6781491738e220083659b5548750679cf9656018b5da56467840851420'),
    'US21': ('48ce523d5da184b8c8aff25704416e23b27efcd581e6426a913e0c349f0367ac', '76777f5e1c32b1706ee4500bf4f563fe7518618ae18d16450cdf81fe62effcc8', 'a9169097cc14c0b23ab943ce95c2254300a88113a05d04ab3803fa4ba15ce894'),
    'US22': ('22afb3bdafb4b04c6f62b3c26af697f103fb1c0c762472852f3e3b952d429565', '80757d6c0da9b604c6fc1f4ca6b4eb8a4b1aa8b2295b5cc62fa9376280ab1148', 'f01d296b69b6ce2eb79ff7ef4022d579e380d135ba588d3fd3455aeac563e154'),
    'US23': ('4680adbc5f911a3fae710696581479bfa94f2d398668f9cb12175dca6ec99066', '74e31220d92765724240a3d50f58bba8735e004180bb0620d3a834402941c542', '8c705e85e067f1c5fabfbe6f73ccf2297753ca5df8e21d57c3c2017f4eeebc6d'),
    'US24': ('6ac2ab5d62d4b82ef29cf06de5d619b218835d80a510983a6616e3f39ef7e8e9', 'e64ceb7d68d67fb91c0e57835c2e7ebafa8fa28949faf9c187fa814fa7cc4cf1', 'f9dc57653c0f979d02f8ea9de9c4dd6c392cba83c59ecdab9710b6ada0252ae6'),
    'US25': ('0daad7e97913ef3d92a9b960caed558548783d27bea2b2e883bad77860e4ae28', '7fc3485639e9c44fcc4a93464f602d8503ba5222c9b213acdce14a08779bc3dc', '84ce4b5fd8eed6725f633a9ee397b44aeaa50ecd4caaf921dc5204029a40bcff'),
    'US26': ('13a8a0f00edb7d67b61a782537332b5e6c214a1038888713747d4ff57726cc7f', 'b6fe4a8b033f4d0601ff58668627f25c8440877578029d35ad9624dee8ba3bec', 'ebf05a050f8c7a25de297031ea4ffd607c9495de2e707004978ed274b6d656b8'),
    'US27': ('0a5b8b9755a6cd923fb287f4759aea4bf903a24e7f0e9c9923f58551281856d1', '5411c3abb05aebe2fbc5872f9b20ec79504614c15b9a54c230f6ac0c371f914b', '763f3700130487e5afb4658441debaa6de4ecd216d9f0aa5878712460cb09b87'),
    'US28': ('b7956f99a86542f9612eb107af9cbfd049304fd41574259dfe42231506834ed5', 'bb15a6ef0ec0f3d6f8bd91d39afbffdbfcab025becc99cc1bc9c64d2db49e074', 'fa37fae93ab19db0fc6f0ee9f27e4077a1752de09e00672d1689e261eeb86887'),
    'US29': ('442dcb4ab20e00ddfc6ac208bd28a2512110948f206191b394b6f140856eedb5', '9f01b42982f5cce1c4f8d297a78ab2c7b4ae193c6da596ec8bf9c44815f21818', 'd9d2a8fb7b91db6ea29ca1c87bf35de3616d86df3ab19dde260dd8ec4f588ebc'),
    'US30': ('118ad5d908d6f10d7b22cb8e20bd25a566e8b15e6e93ae82fade174199acfa5e', '9b3e2b62671052a7316f05213d01d7a8d82f79aaccac1c7ad50b58741411130b', 'f6026d42b473be63c555605c3a6b0b866ee7bf8fe04650a51a88e1e793e05fd7'),
    'US31': ('387c4801389f27736834ce2445094100c647c403ffa0d1e695e83b5776153e36', '6e57506033cc79ad55a8d20a8a4554924598c95cc90a326e58173b06d1051490', 'f48eaafd29665a7d41f484069918885010a0cc2a7cd5384f10fa583ac69dea51'),
    'US32': ('1f3b087b58d8fd4edfa98f2da472d396696c01551e404bbc85ea6aad0bd2293d', '35d1ab11a1f95a51fb3ae94384a4582b9de154f30ff4f86138b0dbd730a6be50', 'ea24d0245f2681019dfa561a95b84a6d510ef4029eaa13842b08b218b751e0b0'),
    'US33': ('3a6c0a4c3aedfe63fc4c7a27353bc208cf8e7a779f2e08853ddc0201e231f49d', '497858ef876b58e649684e1dbc3590993bd0249f2b246927ce92127b2dbb0857', '7ad5dce7372bf3cc7bdd3567942633fc663791ff305201501639324bff1bbc8a'),
    'US34': ('3986a120bd393944e964a0de293bad77eeeb03a99eff605dc2915144237ade08', '837b8d5385234921329285e98ab07d087ebcd78cf12f06a3586533f11a8f53fd', 'ec3c5bd7a60efa462c7296fee613165fbaa54c956846437bd495069dc2bd7c0a'),
    'US35': ('38f4e8b7ff2abb6a1fc36cf73030545be9edf02b58447a9bb50adcbba566af3c', '755ded99a8186539f51044dccbd6f95ac3edbe334d5919352271709f08bf064d', 'cd71a3f72ddfaacd13099d78bbf810bc3aaa5e8dcfecd3e789a292c6723bee93'),
    'US36': ('7315c34e73ce471fc9e18a1eecd95f08c220df10dbdb21c0aa49259d882333f8', 'ef4a77a3aa340305818fb05cb3763698b032e9c09b78e6daf5e43146c01b60c3', 'f75e8035241219f507d7df7eb1c61f8fdfa714acd24ed5702b7cacd74d254131'),
    'US37': ('59fb3b473685038b41f1de7de8d9374c453d68ab4df85773f3f50e4e0c4a38d5', 'a7ce4f8914527923f2d9a056ce595f22e7dcf9edbc2f752a905f7f6bc6afd3cb', 'ca5cf534676b56407a03a35851194223c0cb1f42a248cd80ded0a852e5347f3f'),
    'US38': ('84c6384a3729fcd3e9cb1facbcb5dbc925e69bc743b9e71ece1a83a852bbc42e', 'ba0fb5fe46c65b006a438765b386d09217652bf3087360c90776c5c9ad7f76db', 'e51b6e3c4fa919a5c29795306df2b2154272eb99ac9a6898f000a66fc5f7d701'),
    'US39': ('22398e512d7d2fd4e8410941a73402e6de88c1def8eebd55f7f838a9fc425bd3', 'f1da3bfc543d62ae4183a55e21dcae8ecf52ab738dc403782cd0cefaf7e8e622'),
}


def normalise(body):
    return re.sub(r'(?m)^- \[[xX ]\]', '- [ ]', body.replace('\r\n', '\n')).strip()


def comparison_key(body):
    return '\n'.join(text_key(line) for line in normalise(body).splitlines())


def marked(body):
    return f'{BEGIN}\n{body.strip()}\n{END}'


def text_key(text):
    for _ in range(2):
        try:
            decoded = text.encode('cp1252').decode('utf-8')
        except (UnicodeError, LookupError):
            break
        if decoded == text:
            break
        text = decoded
    return text.strip()


def remove_old_section(body):
    lines = body.replace('\r\n', '\n').splitlines(keepends=True)
    kept, checks = [], []
    skipping = False
    for line in lines:
        if text_key(line) == HISTORY:
            skipping = True
            continue
        if skipping and (line.startswith('## ') or line.strip() == END):
            skipping = False
        if skipping:
            if not line.strip():
                continue
            match = re.fullmatch(r'- \[[xX]\] (.+)', line.rstrip('\n'))
            if not match:
                raise ValueError('Zusätzlicher Text im zu entfernenden Kriterienabschnitt; bitte manuell prüfen')
            checks.append(match.group(1))
        else:
            kept.append(line)
    return ''.join(kept), checks


def migrate_body(current, story):
    """Only replace known template text; preserve notes outside managed section."""
    current, saved_checks = remove_old_section(current)
    if BEGIN in current or END in current:
        if current.count(BEGIN) != 1 or current.count(END) != 1 or current.index(BEGIN) > current.index(END):
            raise ValueError('Ungültige Verwaltungsmarkierungen')
        prefix, rest = current.split(BEGIN, 1)
        active, suffix = rest.split(END, 1)
    else:
        prefix, active, suffix = '', current, ''
    known = [story['body'], story.get('previous_body')]
    if (comparison_key(active) not in [comparison_key(x) for x in known if x]
            and hashlib.sha256(comparison_key(active).encode('utf-8')).hexdigest()
            not in TEMPLATE_HASHES.get(story.get('id'), ())):
        raise ValueError('Beschreibung enthält eigene oder unbekannte Änderungen; Vorschlag manuell zusammenführen')
    checked = re.findall(r'(?m)^- \[[xX]\] (.+)$', active) + saved_checks
    checked = {text_key(line) for line in checked}
    target = story['body'].strip()
    target = '\n'.join('- [x] '+line[6:] if line.startswith('- [ ] ') and text_key(line[6:]) in checked
                       else line for line in target.splitlines())
    return prefix+marked(target)+suffix


def gh(*args):
    result = subprocess.run(['gh', *args], check=True, text=True, encoding='utf-8', capture_output=True)
    return result.stdout


def list_issues(repo):
    # Pagination avoids confusing a missing page with a missing issue.
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/issues?state=all&per_page=100'))
    return [row for page in pages for row in page if 'pull_request' not in row]


def select_issue(rows, story_id):
    matches = [r for r in rows if re.match(r'^'+re.escape(story_id)+r':(?:\s|$)', r['title'])]
    if len(matches) > 1:
        raise ValueError(f'{story_id}: Mehrere passende Issues; keine automatische Zuordnung')
    return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['create', 'update'])
    parser.add_argument('repo', nargs='?', default='Cancani/diplomarbeit')
    parser.add_argument('--apply', action='store_true', help='Vorschläge auf GitHub anwenden')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Repository muss OWNER/REPO sein')
    stories = json.loads((ROOT/'scripts/backlog.json').read_text(encoding='utf-8-sig'))
    rows = list_issues(args.repo)
    folder = ROOT/'issue-preview'/args.repo.replace('/', '_')/args.mode
    folder.mkdir(parents=True, exist_ok=True)
    unresolved = 0
    changes = 0
    for story in stories:
        sid = story['id']
        try:
            issue = select_issue(rows, sid)
        except ValueError as error:
            print(error); unresolved += 1; continue
        if args.mode == 'create':
            if issue:
                print(f'{sid}: vorhanden #{issue["number"]}'); continue
            body = marked(story['body'])
        else:
            if issue is None:
                print(f'{sid}: fehlt, mit create anlegen'); continue
            try:
                body = migrate_body(issue.get('body') or '', story)
            except ValueError as error:
                (folder/f'{sid}-vorschlag.md').write_text(marked(story['body'])+'\n', encoding='utf-8')
                print(f'{sid}: {error}'); unresolved += 1; continue
        path = folder/f'{sid}.md'
        path.write_text(body+'\n', encoding='utf-8')
        before = issue.get('body') or '' if issue else ''
        diff = ''.join(difflib.unified_diff(before.splitlines(True), body.splitlines(True), fromfile='GitHub', tofile='Vorschlag'))
        (folder/f'{sid}.diff').write_text(diff, encoding='utf-8')
        print(f'{sid}: {"anlegen" if not issue else "prüfen"}, Sprint {story["sprint"]}, {story["points"]} SP, {path.relative_to(ROOT)}')
        if not args.apply:
            continue
        if issue and issue['state'] == 'closed':
            print(f'{sid}: geschlossen, keine automatische Änderung'); continue
        if issue:
            # Read again immediately before writing; refuse observed concurrent edits.
            fresh = json.loads(gh('api', f'repos/{args.repo}/issues/{issue["number"]}'))
            fields = ('body', 'title', 'state', 'updated_at')
            if any(fresh.get(k) != issue.get(k) for k in fields):
                print(f'{sid}: zwischenzeitlich geändert, übersprungen'); unresolved += 1; continue
            command = ['issue', 'edit', str(issue['number']), '--repo', args.repo]
        else:
            command = ['issue', 'create', '--repo', args.repo]
        command += ['--title', story['title'], '--body-file', str(path), '--milestone', f'Sprint {story["sprint"]}']
        labels = ','.join(['story', story['epic'], story['priority']])
        command += ['--add-label' if issue else '--label', labels]
        if issue:
            current_labels = {x['name'] for x in issue.get('labels', [])}
            remove = sorted(current_labels & {'must','should','could','wont'} - {story['priority']})
            if remove: command += ['--remove-label', ','.join(remove)]
        gh(*command)
        changes += 1
    print(f'{changes} GitHub-Änderungen, {unresolved} manuell zu prüfende Konflikte. Project-Felder separat pflegen.')
    return 2 if unresolved else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as error:
        # Avoid echoing server responses that may include private issue text.
        print(f'GitHub-Abfrage oder lokaler Aufruf fehlgeschlagen: {type(error).__name__}', file=sys.stderr)
        sys.exit(1)

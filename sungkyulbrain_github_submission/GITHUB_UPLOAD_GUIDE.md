# GitHub 제출 방법

## 1. 새 저장소 생성

GitHub에서 새 Repository를 만든다.

추천 저장소 이름:

```text
seonggyeol-brain-server-web
```

또는

```text
blackice-server-web-summary
```

## 2. 파일 업로드

압축을 푼 뒤 아래 파일과 폴더를 GitHub에 업로드한다.

```text
README.md
docs/
src/
.gitignore
.env.example
GITHUB_UPLOAD_GUIDE.md
```

GitHub 웹에서 업로드하는 경우:

1. 저장소 접속
2. Add file 클릭
3. Upload files 클릭
4. 압축 해제한 파일 전체 업로드
5. Commit changes 클릭

## 3. 제출 문구 예시

```text
개인 담당 부분인 Server/Database, Front/UI, AWS EC2 서버 구축, DynamoDB·AI·Web 연동 흐름, Python 시연 코드 정리 내용을 GitHub에 업로드했습니다.

GitHub 링크:
https://github.com/본인아이디/seonggyeol-brain-server-web
```

## 4. 주의사항

다음 정보는 절대 GitHub에 올리지 않는다.

- AWS API Key
- AWS Secret Key
- SSH pem 키 파일
- 서버 IP 주소
- 서버 DNS 주소
- 실제 DB 파일
- .env 파일
